import os
import tempfile
import subprocess
from typing import TypeVar

from psutil import Process

from chiasma.util.id import IdentSpec, ensure_ident_or_generate

from amino import do, Do, Maybe, __, _, Path, IO, L, List, Boolean, Lists, Nil
from amino.dat import Dat
from amino.case import Case
from amino.logging import module_log

from ribosome.compute.api import prog
from ribosome.compute.program import Program
from ribosome.nvim.io.state import NS
from ribosome.process import Subprocess, SubprocessResult
from ribosome.compute.ribosome_api import Ribo
from ribosome.compute.ribosome import Ribosome
from ribosome.compute.prog import Prog

from myo.util import Ident
from myo.config.handler import find_handler
from myo.data.command import (Command, Interpreter, SystemInterpreter, ShellInterpreter, VimInterpreter, Pid,
                              RunningCommand)
from myo.components.ui.compute.pane import ui_pane_by_ident
from myo.command.run_task import (RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, VimTaskDetails,
                                  SystemTaskDetails, is_system_task)
from myo.components.command.compute.history import push_history
from myo.command.run_task import RunTask
from myo.components.command.data import CommandData
from myo.components.ui.compute.open_pane import open_pane, OpenPaneOptions
from myo.config.component import MyoComponent
from myo.env import Env
from myo.components.command.compute.tpe import CommandRibosome
from myo.command.history import history_entry
from myo.util.id import ensure_ident_prog

log = module_log()
D = TypeVar('D')


def internal_can_run(task: RunTask) -> Boolean:
    return Boolean.isinstance(task.details, SystemTaskDetails)


class run_task(Case, alg=RunTaskDetails):

    def __init__(self, task: RunTask) -> None:
        self.task = task

    @do(NS[D, None])
    def system_task_details(self, details: SystemTaskDetails) -> Do:
        def popen(exe: str, args: List[str]) -> IO[SubprocessResult[None]]:
            return Subprocess(Path(exe), args, None, None).execute(stderr=subprocess.STDOUT)
        parts = yield NS.from_either(
            self.task.command.lines
            .map(Lists.tokens)
            .traverse(lambda a: a.detach_head, Maybe)
            .to_either(lambda: f'empty command line in {self.task.command}')
        )
        result = yield NS.from_io(parts.traverse2(popen, IO))
        output = result.flat_map(_.stdout)
        yield NS.from_io(IO.delay(self.task.log.write_text, output.join_lines))
        yield NS.unit

    @do(NS[D, None])
    def case_default(self, details: RunTaskDetails) -> Do:
        yield NS.unit


@prog.unit
@do(NS[None, None])
def run_internal_command(task: RunTask) -> Do:
    yield run_task(task)(task.details)


def process_alive(pid: Pid) -> IO[bool]:
    return IO.delay(Process, pid.value).replace(True).recover(lambda a: False)


@prog
@do(NS[CommandRibosome, bool])
def command_running(cmd: Command) -> Do:
    running_cmd = yield Ribo.inspect_comp(lambda a: a.running.find(lambda b: b.ident == cmd.ident))
    pid = running_cmd.flat_map(lambda a: a.pid)
    running = pid.cata(process_alive, IO.pure(False))
    yield NS.from_io(running)


class RunCommandOptions(Dat['RunCommandOptions']):

    @staticmethod
    def cons(
            interpreter: str=None,
            langs: List[str]=None,
    ) -> 'RunCommandOptions':
        return RunCommandOptions(Maybe.optional(interpreter), Maybe.optional(langs))

    def __init__(
            self,
            interpreter: Maybe[str],
            langs: Maybe[List[str]],
    ) -> None:
        self.interpreter = interpreter
        self.langs = langs


def system_task_details() -> Prog[SystemTaskDetails]:
    return Prog.pure(SystemTaskDetails())


@do(Prog[RunTaskDetails])
def ui_system_task_details(target: Ident) -> Do:
    pane = yield ui_pane_by_ident(target)
    yield open_pane(pane.ident, OpenPaneOptions())
    return UiSystemTaskDetails(pane)


@do(Prog[RunTaskDetails])
def ui_shell_task_details(cmd_ident: Ident, target: Ident) -> Do:
    shell = yield Ribo.lift_comp(NS.inspect_f(__.command_by_ident(target)), CommandData)
    running = yield command_running(shell)
    if not running:
        yield run_command(shell)
    target = yield Prog.from_maybe(shell.interpreter.target,
                                   lambda: f'shell `{shell.ident}` for command `{cmd_ident}` has no pane')
    pane = yield ui_pane_by_ident(target)
    yield open_pane(pane.ident, OpenPaneOptions())
    return UiShellTaskDetails(shell, pane)


class run_task_details(Case[Interpreter, Program[RunTaskDetails]], alg=Interpreter):

    def __init__(self, cmd: Command) -> None:
        self.cmd = cmd

    @do(Prog[RunTaskDetails])
    def system_interpreter(self, interpreter: SystemInterpreter) -> Do:
        yield interpreter.target / ui_system_task_details | (lambda: system_task_details())

    def shell_interpreter(self, interpreter: ShellInterpreter) -> Program[RunTaskDetails]:
        return ui_shell_task_details(self.cmd.ident, interpreter.target)

    @do(Prog[RunTaskDetails])
    def vim_interpreter(self, interpreter: VimInterpreter) -> Do:
        yield Prog.pure(VimTaskDetails())


@do(IO[Path])
def mk_log_file(base: str) -> Do:
    uid = yield IO.delay(os.getuid)
    tmp_dir = yield IO.delay(tempfile.gettempdir)
    tmp_path = Path(tmp_dir) / f'myo-{uid}' / base
    yield IO.delay(tmp_path.mkdir, exist_ok=True, parents=True)
    (fh, fname) = yield IO.delay(tempfile.mkstemp, prefix='pane-', dir=str(tmp_path))
    return Path(fname)


@do(NS[CommandRibosome, Path])
def insert_log(ident: Ident) -> Do:
    base = yield Ribo.inspect_comp(_.uuid)
    path = yield NS.from_io(mk_log_file(str(base)))
    yield Ribo.modify_comp(__.log(ident, path))
    return path


@do(NS[CommandRibosome, Path])
def task_log(ident: Ident) -> Do:
    existing = yield Ribo.inspect_comp(__.log_by_ident(ident))
    yield existing / NS.pure | L(insert_log)(ident)


@do(NS[CommandRibosome, Path])
def store_running_command(cmd: Command, pid: Maybe[Pid], system: bool) -> Do:
    current = yield Ribo.inspect_comp(lambda a: a.running)
    new = current.filter_not(lambda a: a.ident == cmd.ident).cat(RunningCommand(cmd.ident, pid, system))
    yield Ribo.modify_comp(lambda a: a.set.running(new))


@do(Prog[None])
def run_command(cmd: Command) -> Do:
    task_details = yield run_task_details(cmd)(cmd.interpreter)
    cmd_log = yield Ribo.lift(task_log(cmd.ident), CommandData)
    task = RunTask(cmd, cmd_log, task_details)
    handler = yield find_handler(__.run(task), str(task))
    log.debug(f'running `{task}` with `{handler}`')
    yield Ribo.autocmd_prog('MyoRunCommand')
    pid = yield handler(task)
    yield Ribo.lift(store_running_command(cmd, pid, is_system_task(task_details)), CommandData)
    yield push_history(cmd, cmd.interpreter) if cmd.history else Prog.unit


@prog
def command_by_ident(ident: Ident) -> NS[Ribosome[Env, MyoComponent, CommandData], Command]:
    return Ribo.inspect_comp_e(__.command_by_ident(ident))


@prog.do(None)
def run(ident_spec: IdentSpec, options: RunCommandOptions) -> Do:
    ident = yield ensure_ident_prog(ident_spec)
    cmd = yield command_by_ident(ident)
    yield run_command(cmd)


class RunLineOptions(Dat['RunLineOptions']):

    def __init__(
            self,
            pane: Maybe[Ident],
            shell: Maybe[Ident],
            line: Maybe[str],
            lines: Maybe[List[str]],
            langs: Maybe[List[str]],
            history: Maybe[bool],
    ) -> None:
        self.pane = pane
        self.shell = shell
        self.line = line
        self.lines = lines
        self.langs = langs
        self.history = history


@prog.do(None)
def run_line(options: RunLineOptions) -> Do:
    interpreter = options.shell.cata_f(ShellInterpreter, lambda: SystemInterpreter(options.pane))
    cmd = Command.cons(
        Ident.generate(),
        interpreter,
        lines=options.lines.o(options.line / List) | Nil,
        langs=options.langs | Nil,
        history=options.history | True,
    )
    yield run_command(cmd)


@prog.do(None)
def rerun(index: int=0) -> Do:
    entry = yield Ribo.lift_comp(history_entry(index), CommandData)
    yield run_command(entry.cmd)


__all__ = ('run', 'run_line', 'rerun',)
