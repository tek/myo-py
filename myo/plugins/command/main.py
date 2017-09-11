import re
from uuid import UUID

from ribosome.machine import may_handle, handle, Nop, Message
from ribosome.machine.transition import Fatal
from ribosome.util.callback import parse_callback_spec
from ribosome.machine.base import UnitIO
from ribosome.record import decode_json, encode_json

from myo.state import MyoComponent, MyoTransitions

from amino import L, _, List, Try, __, Maybe, Map, I, IO, Just, Boolean, Left, Either, env
from myo.command import Command, VimCommand, ShellCommand, Shell, CommandJob, TransientCommandJob
from myo.util import amend_options, Ident
from myo.plugins.core.message import Parse, ParseOutput, StageI
from myo.plugins.command.message import (
    Run, ShellRun, Dispatch, AddCommand, AddShellCommand, AddShell, AddVimCommand, SetShellTarget, CommandExecuted,
    RunTest, RunVimTest, CommandAdded, CommandShow, RunLatest, LoadHistory, StoreHistory, RunLine, RunChained,
    RebootCommand, DeleteHistory, CommandHistoryShow
)
from myo.plugins.command.util import assemble_vim_test_line


class Reboot:

    def __init__(self, job) -> None:
        self.job = job

    @property
    def name(self):
        return self.job.name


class CommandTransitions(MyoTransitions):
    _test_cmd_name = '<test>'
    _test_cmd_var = 'create_test_command'

    def _add(self, tpe: type, **strict):
        return self._from_opt(tpe, **strict) / self._add_command

    def _add_command(self, cmd: Command):
        return List(
            self.data.cat(cmd), CommandAdded(cmd, options=self.msg.options)
        )

    @may_handle(StageI)
    def stage_i(self):
        line = self.vim.vars(self._last_test_line_var) | ''
        shell = self.vim.vars(self._last_test_shell_var)
        test_cmd = self.vim.vars.pb(self._test_cmd_var) | Boolean(True)
        opt1 = Map(line=line)
        opt = shell / (lambda a: opt1.cat(('shell', a))) | opt1
        return (
            test_cmd.cata(AddShellCommand(name=self._test_cmd_name, options=opt), Nop()),
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
            self.vim.vars.s(self._history_var) //
            L(decode_json)(_).to_either('failed to load history').lmap(Fatal) /
            self.data.commands.setter.history /
            self.data.setter.commands
        )

    @may_handle(StoreHistory)
    def store_history(self):
        return UnitIO(
            IO.delay(encode_json, self.data.commands.history).join_either /
            L(self).vim.vars.set(self._history_var, _)
        )

    @may_handle(DeleteHistory)
    def delete_history(self) -> Message:
        new = self.data.commands.delete_history(UUID(self.msg.ident))
        return self.data.set(commands=new)

    @handle(AddCommand)
    def add_command(self):
        return self._add(Command, name=self.msg.name)

    @may_handle(AddVimCommand)
    def add_vim_command(self):
        return self._add(VimCommand, name=self.msg.name)

    @handle(AddShellCommand)
    def add_shell_command(self):
        return self._add(ShellCommand, name=self.msg.name)

    @handle(AddShell)
    def add_shell(self):
        return self._from_opt(Shell, name=self.msg.name) / (
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
            self._command_job_fatal(self.msg.command) /
            L(Dispatch)(_, self.msg.options)
        )

    @may_handle(RunLine)
    def run_line(self):
        return Dispatch(ShellCommand(name='run_line',
                                     line=self.msg.args.join_tokens),
                        Map(target=self.msg.target))

    @handle(ShellRun)
    def run_in_shell(self) -> Either[Fatal, Message]:
        line = self.msg.options.get('line') | ''
        def send(cmd):
            return (
                self.data.transient_command(cmd),
                Dispatch(cmd, self.msg.options)
            )
        # double Maybe is necessary - the outer indicates success, the
        # inner is the type of the ShellCommand field
        return (
            self._shell_fatal(self.msg.shell) /
            _.ident /
            Maybe /
            (lambda a: ShellCommand(name='shell_run', shell=a, line=line, transient=True)) /
            send
        )

    @handle(RunLatest)
    def run_latest(self):
        return self.latest_job_fatal / Dispatch

    @handle(RunChained)
    def run_chained(self):
        special_rex = re.compile('s:(.*)')
        def special(name):
            return (
                (
                    self._vim_test_line //
                    L(self._test_line_job)(Map(), _) /
                    List.wrap //
                    _.head
                ).to_either('failed to create test line')
                if name == 'vimtest' else
                Left('invalid special command: {}'.format(name))
            )
        def resolve(name):
            return (
                Maybe(special_rex.match(name)).cata(
                    L(special)(__.group(1)),
                    lambda: (self.data.command(name) /
                             CommandJob.from_attr('command'))
                )
            )
        def cons(line, job):
            cmd = job.command.set(eval=False)
            return (
                Dispatch(
                    TransientCommandJob(prefix='chained', command=cmd,
                                        override_line=line),
                    Map()
                )
            )
        commands = (
            List.wrap(self.msg.commands) / resolve
        ).sequence(Either)
        lines = ((commands.eff() / __.resolved_line(self.vim)).value //
                 __.sequence(Either))
        chained = (
            (self._callback('chainer') & lines)
            .map2(lambda a, b: a(b))
            .to_either('chainer failed')
        )
        return (
            (chained & (commands // __.head.to_either('commands empty')))
            .map2(cons)
            .lmap(Fatal)
        )

    @handle(RebootCommand)
    def reboot_command(self):
        return (
            self._command_job_fatal(self.msg.command) /
            Reboot /
            L(Dispatch)(_, self.msg.options)
        )

    @handle(Dispatch)
    def dispatch(self):
        cmd = self.msg.command
        self.vim.vars.set_p('last_command', dict(name=cmd.name))
        self.vim.pautocmd('RunCommand')
        return self.data.dispatch_message(cmd, self.msg.options) / _.pub

    @may_handle(CommandExecuted)
    def command_executed(self):
        job = self.msg.job
        def set_log(path, cmd_lens):
            def run(cmd):
                self.log.debug('setting {} log to {}'.format(cmd.name, path))
                return cmd.set(log_path=Just(path))
            return cmd_lens.modify(run)
        data = (
            (self.msg.log_path.to_either('no log path') &
             self.data.command_lens(job.main_key))
            .map2(set_log) |
            self.data
        )
        if job.history:
            new = data.commands.add_history(job)
            return data.set(commands=new), StoreHistory()

    @handle(Parse)
    def parse(self):
        def find_log(c):
            return ((self.data.command(c.main_key) // _.log_path)
                    .to_either('{} has no log'.format(c)))
        def parse(c, l):
            self.log.debug('parsing {} from {}'.format(c, l))
            return (
                Try(l.read_text) /
                List.lines /
                L(ParseOutput)(c, _, l, self.msg.options) /
                _.pub
            )
        cmd = (
            self.msg.options.get('command')
            .cata(
                L(self.data.command_or_job)(_),
                lambda: self.latest_job_fatal / Left
            ) / __.left_or_map(lambda a: CommandJob(command=a))
        )
        log_path = cmd // find_log
        return (cmd & log_path).flat_map2(parse).lmap(Fatal)

    @handle(RunTest)
    def run_test(self):
        opt = self.msg.options
        return (
            opt.get('ctor')
            .to_either('no test ctor specified') //
            self._assemble //
            L(self._test_line_dispatch)(opt - 'ctor', _)
        ).to_either('failed to setup test line').lmap(Fatal)

    @handle(RunVimTest)
    def run_vim_test(self):
        return (
            self._vim_test_line //
            L(self._test_line_dispatch)(self.msg.options, _)
        ).lmap(Fatal)

    @may_handle(CommandShow)
    def show(self):
        msg = self.data.commands.commands / _.desc
        self.log.info(msg.join_lines)

    @may_handle(CommandHistoryShow)
    def history_show(self):
        msg = self.data.commands.history / _.desc
        self.log.info(msg.join_lines)

    def _command_job_fatal(self, ident):
        return (self.data.command_or_job(self.msg.command)
                .lmap(Fatal) /
                __.left_or_map(CommandJob.from_attr('command')))

    def _shell_fatal(self, ident: Ident) -> Either[str, Shell]:
        return self.data.shell(ident).lmap(Fatal)

    @property
    def latest_job_fatal(self):
        return self.data.commands.latest_command.lmap(Fatal)

    def _assemble(self, ctor):
        return parse_callback_spec(ctor) // __(self.vim)

    @property
    def _vim_test_line(self):
        return assemble_vim_test_line(self.vim)

    def _test_line_dispatch(self, options, line):
        return self._test_line_job(options, line).map2(Dispatch)

    def _test_line_job(self, options, line):
        def dispatch(cmd, line, langs, opt):
            shell = opt.get('shell')
            job = TransientCommandJob(prefix='test_line', command=cmd,
                                      override_line=line, override_langs=langs,
                                      override_shell=shell)
            return job, opt
        return self._test_line_params(options, line).map4(dispatch)

    def _test_line_params(self, options, line):
        glangs = self.vim.buffer.vars.pl('test_langs')
        langs = options.get('langs').or_else(glangs) | List()
        shell = self.vim.buffer.pvar_or_global('test_shell')
        target = self.vim.buffer.pvar_or_global('test_target')
        opt = amend_options(options, 'shell', shell)
        opt2 = amend_options(opt, 'target', target) + ('langs', langs)
        self.vim.vars.set(self._last_test_line_var, line)
        shell / L(self.vim.vars.set)('Myo_last_test_shell', _)
        return (
            self.data.command(self._test_cmd_name)
            .to_either('no test command') /
            (lambda a: (a, line, langs, opt2))
        )


class Plugin(MyoComponent):
    Transitions = CommandTransitions

    def new_state(self):
        pass

__all__ = ('Plugin', 'AddVimCommand', 'AddCommand', 'Run', 'AddShell',
           'AddShellCommand', 'SetShellTarget')
