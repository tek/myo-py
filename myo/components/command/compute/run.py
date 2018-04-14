import os
import tempfile
import subprocess
from typing import TypeVar

from chiasma.util.id import IdentSpec, ensure_ident

from amino import do, Do, Maybe, __, _, Path, IO, L, List, Boolean, Lists, Nil
from amino.dat import Dat
from amino.case import Case

from ribosome.compute.api import prog
from ribosome.compute.prog import Program, Prog
from ribosome.nvim.io.state import NS
from ribosome.process import Subprocess, SubprocessResult
from ribosome.compute.ribosome_api import Ribo
from ribosome.compute.ribosome import Ribosome

from myo.util import Ident
from myo.config.handler import find_handler
from myo.data.command import Command, Interpreter, SystemInterpreter, ShellInterpreter, VimInterpreter
from myo.components.ui.compute.pane import ui_pane_by_ident
from myo.command.run_task import (RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, VimTaskDetails,
                                  SystemTaskDetails)
from myo.components.command.compute.history import push_history
from myo.command.run_task import RunTask
from myo.components.command.data import CommandData
from myo.components.ui.compute.open_pane import open_pane, OpenPaneOptions
from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.env import Env
from myo.components.command.compute.tpe import CommandRibosome

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


@prog.unit
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
    yield run_command_1(shell)
    target = yield Prog.from_maybe(shell.interpreter.target,
                                   f'shell `{shell.ident}` for command `{cmd_ident}` has no pane')
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


@do(Prog[None])
def run_command_1(cmd: Command) -> Do:
    task_details = yield run_task_details(cmd)(cmd.interpreter)
    log = yield Ribo.lift(task_log(cmd.ident), CommandData)
    task = RunTask(cmd, log, task_details)
    handler = yield find_handler(__.run(task), str(task))
    yield handler(task)
    yield push_history(cmd, cmd.interpreter)


# TODO allow prog to reuse previous Ribosome component affiliation
@prog
def command_by_ident(ident: Ident) -> NS[Ribosome[MyoSettings, Env, MyoComponent, CommandData], Command]:
    return Ribo.inspect_comp_e(__.command_by_ident(ident))


@prog.do
@do(Prog[None])
def run_command(ident_spec: IdentSpec, options: RunCommandOptions) -> Do:
    ident = ensure_ident(ident_spec)
    cmd = yield command_by_ident(ident)
    yield run_command_1(cmd)


class RunLineOptions(Dat['RunLineOptions']):

    def __init__(self, pane: Maybe[Ident], shell: Maybe[Ident], lines: List[str], langs: Maybe[List[str]]) -> None:
        self.pane = pane
        self.shell = shell
        self.lines = lines
        self.langs = langs


@prog.do
@do(Prog[None])
def run_line(options: RunLineOptions) -> Do:
    interpreter = options.shell.cata_f(ShellInterpreter, lambda: SystemInterpreter(options.pane))
    cmd = Command.cons(Ident.generate(), interpreter, lines=options.lines, langs=options.langs | Nil)
    yield run_command_1(cmd)


__all__ = ('run_command', 'run_line')
