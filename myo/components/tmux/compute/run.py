from amino import do, Do, Boolean, Path, Just, L, _, Maybe
from amino.lenses.lens import lens
from amino.case import Case

from chiasma.io.state import TS
from chiasma.data.tmux import TmuxData
from chiasma.pane import pane_by_ident
from chiasma.commands.pane import send_keys, pipe_pane

from ribosome.compute.api import prog
from ribosome.config.component import ComponentData
from ribosome.compute.prog import Program, Prog
from ribosome.nvim.io.state import NS

from myo.env import Env
from myo.command.run_task import RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, RunTask
from myo.data.command import Command
from myo.ui.data.view import Pane


@do(TS[ComponentData[Env, TmuxData], None])
def run_system_task(cmd: Command, pane: Pane, log_path: Maybe[Path]) -> Do:
    tpane = yield pane_by_ident(pane.ident).zoom(lens.comp)
    id = yield TS.from_maybe(tpane.id, f'no tmux id for pane {pane.ident}')
    yield log_path / L(pipe_pane)(id, _) / TS.lift | TS.unit
    yield TS.lift(send_keys(id, cmd.lines))


class run_task_in_pane(Case, alg=RunTaskDetails):

    def __init__(self, task: RunTask) -> None:
        self.task = task

    @do(TS[ComponentData[Env, TmuxData], None])
    def ui_system_task_details(self, details: UiSystemTaskDetails) -> Do:
        yield run_system_task(self.task.command, details.pane, Just(self.task.log))

    @do(TS[ComponentData[Env, TmuxData], None])
    def ui_shell_task_details(self, details: UiShellTaskDetails) -> Do:
        yield run_system_task(self.task.command, details.pane, Just(self.task.log))

    def case_default(self, task: RunTaskDetails) -> TS:
        yield TS.error(f'cannot run {task} in tmux')


@prog.unit
@do(NS[ComponentData[Env, TmuxData], None])
def run_in_pane(task: RunTask) -> Do:
    yield run_task_in_pane(task)(task.details).nvim
    yield NS.pure(None)


@prog.do
@do(Prog)
def run_command(task: RunTask) -> Do:
    yield run_in_pane(task)


def tmux_can_run(task: RunTask) -> Boolean:
    return isinstance(task.details, (UiSystemTaskDetails, UiShellTaskDetails))


__all__ = ('run_command', 'tmux_can_run')
