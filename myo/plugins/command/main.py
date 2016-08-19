from collections import namedtuple

from ribosome.machine import may_handle, handle, Nop, either_msg, either_handle

from myo.state import MyoComponent, MyoTransitions

from amino import L, _, List, Try, __, Maybe, curried
from myo.command import Command, VimCommand, ShellCommand, Shell
from myo.util import optional_params, parse_callback_spec
from myo.plugins.core.message import Parse, ParseOutput
from myo.plugins.command.message import (Run, ShellRun, Dispatch, AddCommand,
                                         AddShellCommand, AddShell,
                                         AddVimCommand, SetShellTarget,
                                         CommandExecuted, RunTest, RunVimTest)
from myo.plugins.command.util import assemble_vim_test_line

RunInShell = namedtuple('RunInShell', ['shell'])


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        @property
        def _cmd_opt(self):
            return List('parser')

        def _create(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
                    **strict):
            o = self.msg.options
            opt = optional_params(o, *opt_keys)
            missing = lambda: mand_keys.filter(o.has_key)
            err = lambda: 'cannot create {} without params: {}'.format(missing)
            mand = o.get_all_map(*mand_keys).to_either(err)
            return mand / (lambda a: tpe(**a, **opt, **strict))

        def _add(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
                 **strict):
            return (
                self._create(tpe, mand_keys, opt_keys, **strict) /
                self.data.cat
            )

        @handle(AddCommand)
        def add_command(self):
            return self._add(Command, List('line'), self._cmd_opt,
                             name=self.msg.name)

        @may_handle(AddVimCommand)
        def add_vim_command(self):
            return self._add(VimCommand, List('line'), self._cmd_opt,
                             name=self.msg.name)

        @handle(AddShellCommand)
        def add_shell_command(self):
            return self._add(ShellCommand, List('line'),
                             self._cmd_opt.cat('shell'), name=self.msg.name)

        @handle(AddShell)
        def add_shell(self):
            mand = List('line')
            opt = List('target')
            return self._create(Shell, mand, opt, name=self.msg.name) / (
                lambda shell: (
                    self.data + shell,
                    shell.target / L(SetShellTarget)(shell, _) / _.pub | Nop
                )
            )

        @handle(Run)
        def run(self):
            return (
                self.data.command(self.msg.command) /
                L(Dispatch)(_, self.msg.options)
            )

        @handle(ShellRun)
        def run_in_shell(self):
            line = self.msg.options.get('line') | ''
            # double Maybe is necessary - the outer indicates success, the
            # inner is the type of the ShellCommand field
            return (
                self.data.shell(self.msg.shell) /
                _.uuid /
                Maybe /
                (lambda a: ShellCommand(name='shell_run', shell=a, line=line,
                                        transient=True)) /
                L(Dispatch)(_, self.msg.options)
            )

        @handle(Dispatch)
        def dispatch(self):
            cmd = self.msg.command
            return (
                self.data.dispatch_message(cmd, self.msg.options) /
                _.pub /
                (lambda a: (a, CommandExecuted(cmd)))
            )

        @may_handle(CommandExecuted)
        def command_executed(self):
            new = self.data.commands.add_history(self.msg.command.uuid)
            return self.data.set(commands=new)

        @handle(Parse)
        def parse(self):
            cmd = (
                self.msg.options.get('command')
                .cata(self.data.command, self._latest_command)
                .to_either('invalid command name or empty history')
            )
            log_path = cmd // __.log_path.to_either('command has no log')
            def parse(c, l):
                return (
                    Try(l.read_text) /
                    __.splitlines() /
                    List.wrap /
                    L(ParseOutput)(c, _, self.msg.options) /
                    _.pub
                )
            return (cmd & log_path).flat_map2(parse)

        @handle(RunTest)
        def run_test(self):
            opt = self.msg.options
            return (
                opt.get('ctor') //
                self._assemble /
                self._run_test_line(opt - 'ctor')
            )

        @either_handle(RunVimTest)
        def run_vim_test(self):
            return (
                assemble_vim_test_line(self.vim) //
                __.head.to_either('vim-test failed') /
                self._run_test_line(self.msg.options)
            )

        def _latest_command(self):
            return self.data.commands.history.head // self.data.command

        def _assemble(self, ctor):
            return parse_callback_spec(ctor).join / (lambda a: a())

        @curried
        def _run_test_line(self, options, line):
            cmd = ShellCommand(name='test', line=line, transient=True)
            return Dispatch(cmd, options)

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand', 'Run', 'AddShell',
           'AddShellCommand', 'SetShellTarget')
