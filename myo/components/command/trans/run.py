import os
import tempfile
import subprocess
from typing import TypeVar

from chiasma.util.id import IdentSpec, ensure_ident

from amino import do, Do, Maybe, __, _, Path, IO, L, List, Boolean, Lists
from amino.state import EitherState, State

from amino.dat import Dat
from amino.case import Case
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.trans.action import Trans
from ribosome.nvim.io.state import NS
from ribosome.process import Subprocess, SubprocessResult

from myo.util import Ident
from myo.config.handler import find_handler
from myo.data.command import Command, Interpreter, SystemInterpreter, ShellInterpreter, VimInterpreter
from myo.components.ui.trans.pane import ui_pane_by_ident
from myo.command.run_task import (RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, VimTaskDetails,
                                  SystemTaskDetails)
from myo.components.command.trans.history import push_history
from myo.command.run_task import RunTask
from myo.components.command.data import CommandData
from myo.components.ui.trans.open_pane import open_pane, OpenPaneOptions

D = TypeVar('D')


def internal_can_run(task: RunTask) -> Boolean:
    return Boolean.isinstance(task.details, SystemTaskDetails)


class run_task(Case, alg=RunTaskDetails):

    def __init__(self, task: RunTask) -> None:
        self.task = task

    @do(NS[D, None])
    def system_task_details(self, details: SystemTaskDetails) -> Do:
        def popen(exe: str, args: List[str]) -> IO[SubprocessResult[None]]:
            return Subprocess(Path(exe), args, None).execute(None, stderr=subprocess.STDOUT)
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


@trans.free.unit(trans.st)
@do(NS[None, None])
def run_internal_command(task: RunTask) -> Do:
    yield run_task(task)(task.details)


class RunCommandOptions(Dat['RunCommandOptions']):

    @staticmethod
    def cons(
            interpreter: str=None,
    ) -> 'RunCommandOptions':
        return RunCommandOptions(Maybe.optional(interpreter))

    def __init__(
            self,
            interpreter: Maybe[str],
    ) -> None:
        self.interpreter = interpreter


def system_task_details() -> Trans:
    return Trans.pure(SystemTaskDetails())


@do(Trans[RunTaskDetails])
def ui_system_task_details(target: Ident) -> Do:
    pane = yield ui_pane_by_ident(target)
    yield open_pane(pane.ident, OpenPaneOptions())
    return UiSystemTaskDetails(pane)


@do(Trans[RunTaskDetails])
def ui_shell_task_details(cmd_ident: Ident, target: Ident) -> Do:
    shell = yield State.inspect_f(__.comp.command_by_ident(target)).trans
    yield run_command_1(shell)
    target = yield Trans.from_maybe(shell.interpreter.target,
                                    f'shell `{shell.ident}` for command `{cmd_ident}` has no pane')
    pane = yield ui_pane_by_ident(target)
    yield open_pane(pane.ident, OpenPaneOptions())
    return UiShellTaskDetails(shell, pane)


class run_task_details(Case[Interpreter, Trans[RunTaskDetails]], alg=Interpreter):

    def __init__(self, cmd: Command) -> None:
        self.cmd = cmd

    @do(Trans[RunTaskDetails])
    def system_interpreter(self, interpreter: SystemInterpreter) -> Do:
        yield interpreter.target / ui_system_task_details | (lambda: system_task_details())

    def shell_interpreter(self, interpreter: ShellInterpreter) -> Trans[RunTaskDetails]:
        return ui_shell_task_details(self.cmd.ident, interpreter.target)

    @do(Trans[RunTaskDetails])
    def vim_interpreter(self, interpreter: VimInterpreter) -> Do:
        yield Trans.pure(VimTaskDetails())


@do(IO[Path])
def mk_log_file(base: str) -> Do:
    uid = yield IO.delay(os.getuid)
    tmp_dir = yield IO.delay(tempfile.gettempdir)
    tmp_path = Path(tmp_dir) / f'myo-{uid}' / base
    yield IO.delay(tmp_path.mkdir, exist_ok=True, parents=True)
    (fh, fname) = yield IO.delay(tempfile.mkstemp, prefix='pane-', dir=str(tmp_path))
    return Path(fname)


@do(NS[CommandData, Path])
def insert_log(ident: Ident) -> Do:
    base = yield NS.inspect(_.uuid)
    path = yield NS.from_io(mk_log_file(str(base)))
    yield NS.modify(__.log(ident, path))
    return path


@do(NS[CommandData, Path])
def task_log(ident: Ident) -> Do:
    existing = yield NS.inspect(__.log_by_ident(ident))
    yield existing / NS.pure | L(insert_log)(ident)


@do(Trans[None])
def run_command_1(cmd: Command) -> Do:
    task_details = yield run_task_details(cmd)(cmd.interpreter)
    log = yield task_log(cmd.ident).zoom(lens.comp).trans
    task = RunTask(cmd, log, task_details)
    handler = yield find_handler(__.run(task), str(task))
    yield handler(task)
    yield push_history(cmd, cmd.interpreter)


@trans.free.do()
@do(Trans[None])
def run_command(ident_spec: IdentSpec, options: RunCommandOptions) -> Do:
    ident = ensure_ident(ident_spec)
    cmd = yield EitherState.inspect_f(__.comp.command_by_ident(ident)).trans
    yield run_command_1(cmd)


class RunLineOptions(Dat['RunLineOptions']):

    def __init__(self, pane: Maybe[Ident], shell: Maybe[Ident], lines: List[str], langs: List[str]) -> None:
        self.pane = pane
        self.shell = shell
        self.lines = lines
        self.langs = langs


@trans.free.do()
@do(Trans[None])
def run_line(options: RunLineOptions) -> Do:
    interpreter = options.shell.cata(ShellInterpreter, lambda: SystemInterpreter(options.pane))
    cmd = Command.cons(Ident.generate(), interpreter, lines=options.lines, langs=options.langs)
    yield run_command_1(cmd)


__all__ = ('run_command', 'run_line')
