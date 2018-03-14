import os
import tempfile
import subprocess
from typing import TypeVar

from amino import do, Do, Maybe, __, _, Path, IO, L, List, Boolean, Lists
from amino.state import EitherState, State

from amino.dat import Dat
from amino.dispatch import PatMat
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.trans.action import TransM
from ribosome.nvim.io import NS
from ribosome.process import Subprocess
from ribosome import ribo_log

from myo.util import Ident
from myo.config.handler import find_handler
from myo.data.command import Command, Interpreter, SystemInterpreter, ShellInterpreter, VimInterpreter
from myo.components.ui.trans.pane import ui_pane_by_ident, render_pane
from myo.command.run_task import (RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, VimTaskDetails,
                                  SystemTaskDetails)
from myo.components.command.trans.history import push_history
from myo.command.run_task import RunTask
from myo.components.command.data import CommandData

D = TypeVar('D')


def internal_can_run(task: RunTask) -> Boolean:
    return isinstance(task.details, SystemTaskDetails)


class run_task(PatMat, alg=RunTaskDetails):

    def __init__(self, task: RunTask) -> None:
        self.task = task

    @do(NS[D, None])
    def system_task_details(self, details: SystemTaskDetails) -> Do:
        def popen(exe: str, args: List[str]) -> IO[None]:
            return Subprocess(exe, args, None).execute(None, stderr=subprocess.STDOUT)
        parts = yield NS.from_either(
            self.task.command.lines
            .map(Lists.tokens)
            .traverse(lambda a: a.detach_head, Maybe)
            .to_either(lambda: f'empty command line in {self.task.cmd}')
        )
        result = yield NS.from_io(parts.traverse2(popen, IO))
        output = result.flat_map(_.stdout)
        yield NS.from_io(IO.delay(self.task.log.write_text, output.join_lines))
        yield NS.unit

    def patmat_default(self, details: RunTaskDetails) -> NS[D, None]:
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


def system_task_details() -> TransM:
    return TransM.pure(SystemTaskDetails())


@do(TransM[RunTaskDetails])
def ui_system_task_details(target: Ident) -> Do:
    # ensure_view
    pane = yield ui_pane_by_ident(target).m
    yield render_pane(pane.ident).m
    return UiSystemTaskDetails(pane)


class run_task_details(PatMat[Interpreter, TransM[RunTaskDetails]], alg=Interpreter):

    def __init__(self, cmd: Command) -> None:
        self.cmd = cmd

    @do(TransM[RunTaskDetails])
    def system_interpreter(self, interpreter: SystemInterpreter) -> Do:
        yield interpreter.target / ui_system_task_details | (lambda: system_task_details())

    @do(TransM[RunTaskDetails])
    def shell_interpreter(self, interpreter: ShellInterpreter) -> Do:
        shell = yield State.inspect_f(__.comp.command_by_ident(interpreter.target)).trans
        target = yield TransM.from_maybe(shell.interpreter.target,
                                         f'shell `{shell.ident}` for command `{self.cmd.ident}` has no pane')
        pane = yield ui_pane_by_ident(target).m
        yield render_pane(pane.ident).m
        return UiShellTaskDetails(shell, pane)

    @do(TransM[RunTaskDetails])
    def vim_interpreter(self, interpreter: VimInterpreter) -> Do:
        yield TransM.pure(VimTaskDetails())


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


@trans.free.do()
@do(TransM)
def run_command(ident: Ident, options: RunCommandOptions) -> Do:
    cmd = yield EitherState.inspect_f(__.comp.command_by_ident(ident)).trans
    task_details = yield run_task_details(cmd)(cmd.interpreter)
    log = yield task_log(ident).zoom(lens.comp).trans
    task = RunTask(cmd, log, task_details)
    handler = yield find_handler(__.run(task), str(task)).m
    yield handler(task).m
    yield push_history(cmd, cmd.interpreter.target).m


class RunLineOptions(Dat['RunLineOptions']):

    def __init__(self, pane: Maybe[Ident], lines: List[str], langs: List[str]) -> None:
        self.pane = pane
        self.lines = lines
        self.langs = langs


@trans.free.do()
@do(TransM)
def run_line(options: RunLineOptions) -> Do:
    cmd = Command.cons(Ident.generate(), SystemInterpreter(options.pane), lines=options.lines, langs=options.langs)
    task_details = yield run_task_details(cmd)(cmd.interpreter)
    log = yield task_log(cmd.ident).zoom(lens.comp).trans
    task = RunTask(cmd, log, task_details)
    handler = yield find_handler(__.run(task), str(task)).m
    yield handler(task).m
    yield push_history(cmd, cmd.interpreter.target).m


__all__ = ('run_command', 'run_line')
