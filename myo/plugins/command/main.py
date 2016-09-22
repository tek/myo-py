from collections import namedtuple

from ribosome.machine import may_handle, handle
from ribosome.machine.transition import Fatal

from myo.state import MyoComponent, MyoTransitions

from amino import L, _, List, Try, __, Maybe, curried, Map, Right, I
from myo.command import Command, VimCommand, ShellCommand, Shell
from myo.util import optional_params, amend_options, bool_params
from myo.plugins.core.message import Parse, ParseOutput, StageI
from myo.plugins.command.message import (Run, ShellRun, Dispatch, AddCommand,
                                         AddShellCommand, AddShell,
                                         AddVimCommand, SetShellTarget,
                                         CommandExecuted, RunTest, RunVimTest,
                                         CommandAdded, CommandShow, RunLatest,
                                         LoadHistory, StoreHistory)
from myo.plugins.command.util import assemble_vim_test_line
from myo.util.callback import parse_callback_spec

RunInShell = namedtuple('RunInShell', ['shell'])


class CommandTransitions(MyoTransitions):
    _test_cmd_name = '<test>'

    @property
    def _cmd_opt(self):
        return List('parser')

    @property
    def _cmd_list_opt(self):
        return List('langs', 'signals')

    @property
    def _cmd_bool_opt(self):
        return List('kill')

    def _create(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
                **strict):
        o = self.msg.options
        opt = optional_params(o, *opt_keys + self._cmd_opt)
        opt_list = (optional_params(o, *self._cmd_list_opt)
                    .valmap(_ / List.wrap | List()))
        opt_bool = (bool_params(o, *self._cmd_bool_opt))
        missing = lambda: mand_keys.filter_not(o.has_key)
        err = lambda: 'cannot create {} without params: {}'.format(tpe,
                                                                   missing())
        mand = o.get_all_map(*mand_keys).to_either(err)
        return mand / (lambda a: tpe(**a, **opt, **opt_list, **opt_bool,
                                     **strict))

    def _add(self, tpe: type, mand_keys: List[str], opt_keys: List[str],
             **strict):
        return (
            self._create(tpe, mand_keys, opt_keys, **strict) /
            self._add_command
        )

    def _add_command(self, cmd: Command):
        return List(
            self.data.cat(cmd), CommandAdded(cmd, options=self.msg.options)
        )

    @may_handle(StageI)
    def stage_i(self):
        line = self.vim.vars(self._last_test_line_var) | ''
        shell = self.vim.vars(self._last_test_shell_var)
        opt1 = Map(line=line)
        opt = shell / (lambda a: opt1.cat(('shell', a))) | opt1
        return (
            AddShellCommand(name=self._test_cmd_name, options=opt),
            LoadHistory()
        )

    @property
    def _history_var(self):
        return 'Myo_history'

    @property
    def _last_test_line_var(self):
        return 'Myo_last_test_line'

    @property
    def _last_test_shell_var(self):
        return 'Myo_last_test_shell'

    @handle(LoadHistory)
    def load_history(self):
        return (
            self.vim.vars.s(self._history_var) /
            __.split(',') /
            List.wrap /
            (lambda a: self.data.commands.set(history=a)) /
            self.data.setter.commands
        )

    @may_handle(StoreHistory)
    def store_history(self):
        names = (
            self.data.commands.history /
            self.data.command //
            _.to_maybe /
            _.name
        )
        self.vim.vars.set(self._history_var, names.mk_string(','))

    @handle(AddCommand)
    def add_command(self):
        return self._add(Command, List('line'), List(),
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
                self._add_command(shell) +
                (shell.target / L(SetShellTarget)(shell, _) / _.pub).to_list
            )
        )

    @may_handle(CommandAdded)
    def command_added(self):
        if self.msg.options.get('start').exists(I):
            return Run(self.msg.command.uuid)

    @handle(Run)
    def run(self):
        return (
            self.data.command(self.msg.command) /
            L(Dispatch)(_, self.msg.options)
        )

    @handle(ShellRun)
    def run_in_shell(self):
        line = self.msg.options.get('line') | ''
        def send(cmd):
            return (
                self.data.transient_command(cmd),
                Dispatch(cmd, self.msg.options)
            )
        # double Maybe is necessary - the outer indicates success, the
        # inner is the type of the ShellCommand field
        return (
            self.data.shell(self.msg.shell) /
            _.uuid /
            Maybe /
            (lambda a: ShellCommand(name='shell_run', shell=a, line=line,
                                    transient=True)) /
            send
        )

    @handle(RunLatest)
    def run_latest(self):
        return (
            self.data.commands.latest_command /
            Dispatch
        )

    @handle(Dispatch)
    def dispatch(self):
        cmd = self.msg.command
        self.vim.vars.set_p('last_command', dict(name=cmd.name))
        self.vim.pautocmd('RunCommand')
        return (
            self.data.dispatch_message(cmd, self.msg.options) /
            _.pub /
            (lambda a: (a, CommandExecuted(cmd)))
        )

    @may_handle(CommandExecuted)
    def command_executed(self):
        new = self.data.commands.add_history(self.msg.command.uuid)
        return self.data.set(commands=new), StoreHistory()

    @handle(Parse)
    def parse(self):
        cmd = (
            self.msg.options.get('command')
            .cata(self.data.command, lambda: self.data.commands.latest_command)
            .to_either('invalid command name or empty history')
        )
        def find_log(c):
            return (
                (c.shell // self.data.shell | c)
                .log_path.to_either('{} has no log'.format(c))
            )
        log_path = cmd // find_log
        def parse(c, l):
            self.log.debug('parsing {} from {}'.format(c, l))
            return (
                Try(l.read_text) /
                __.splitlines() /
                List.wrap /
                L(ParseOutput)(c, _, l, self.msg.options) /
                _.pub
            )
        return (cmd & log_path).flat_map2(parse).lmap(Fatal)

    @handle(RunTest)
    def run_test(self):
        opt = self.msg.options
        return (
            opt.get('ctor').to_either(Fatal('no test ctor specified')) //
            self._assemble //
            self._run_test_line(opt - 'ctor')
        ).lmap(Fatal)

    @handle(RunVimTest)
    def run_vim_test(self):
        return (
            assemble_vim_test_line(self.vim) //
            __.head.to_either('vim-test failed') //
            self._run_test_line(self.msg.options)
        )

    @may_handle(CommandShow)
    def show(self):
        msg = self.data.commands.commands / _.desc
        self.log.info(msg.join_lines)

    def _assemble(self, ctor):
        return parse_callback_spec(ctor).join / (lambda a: a())

    @curried
    def _run_test_line(self, options, line):
        glangs = self.vim.buffer.vars.pl('test_langs')
        langs = options.get('langs').or_else(glangs) | List()
        shell = self.vim.buffer.pvar_or_global('test_shell')
        target = self.vim.buffer.pvar_or_global('test_target')
        opt = amend_options(options, 'shell', shell)
        opt2 = amend_options(opt, 'target', target)
        self.vim.vars.set(self._last_test_line_var, line)
        shell / L(self.vim.vars.set)('Myo_last_test_shell', _)
        def dispatch(data):
            return Right(data) & (data.command(self._test_cmd_name) /
                                  L(Dispatch)(_, opt2))
        return (
            self.data.command_lens(self._test_cmd_name)
            .to_either('no test command') /
            __.modify(__.set(line=line, langs=langs)) //
            dispatch
        )


class Plugin(MyoComponent):
    Transitions = CommandTransitions

    def new_state(self):
        pass

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand', 'Run', 'AddShell',
           'AddShellCommand', 'SetShellTarget')
