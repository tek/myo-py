from amino import do, Do, Boolean, Path, Just, L, _, Maybe
from amino.lenses.lens import lens
from amino.case import Case
from amino.logging import module_log

from chiasma.io.state import TS
from myo.components.tmux.data import TmuxData

from chiasma.pane import pane_by_ident
from chiasma.commands.pane import send_keys, pipe_pane

from ribosome.compute.api import prog
from ribosome.config.component import ComponentData
from ribosome.nvim.io.state import NS

from myo.env import Env
from myo.command.run_task import RunTaskDetails, UiSystemTaskDetails, UiShellTaskDetails, RunTask
from myo.data.command import Command, Pid
from myo.ui.data.view import Pane
from myo.tmux.pid import process_pid

log = module_log()


@do(TS[ComponentData[Env, TmuxData], Maybe[Pid]])
def run_system_task(cmd: Command, pane: Pane, log_path: Maybe[Path]) -> Do:
    tpane = yield pane_by_ident(pane.ident).zoom(lens.comp.views)
    id = yield TS.from_maybe(tpane.id, f'no tmux id for pane {pane.ident}')
    yield log_path / L(pipe_pane)(id, _) / TS.lift | TS.unit
    yield TS.lift(send_keys(id, cmd.lines))
    yield TS.lift(process_pid(id))


class run_task_in_pane(Case[RunTaskDetails, Maybe[Pid]], alg=RunTaskDetails):

    def __init__(self, task: RunTask) -> None:
        self.task = task

    @do(TS[ComponentData[Env, TmuxData], Maybe[Pid]])
    def ui_system_task_details(self, details: UiSystemTaskDetails) -> Do:
        yield run_system_task(self.task.command, details.pane, Just(self.task.log))

    @do(TS[ComponentData[Env, TmuxData], Maybe[Pid]])
    def ui_shell_task_details(self, details: UiShellTaskDetails) -> Do:
        yield run_system_task(self.task.command, details.pane, Just(self.task.log))

    @do(TS[ComponentData[Env, TmuxData], Maybe[Pid]])
    def case_default(self, task: RunTaskDetails) -> Do:
        yield TS.error(f'cannot run {task} in tmux')


@prog
@do(NS[ComponentData[Env, TmuxData], Maybe[Pid]])
def run_in_pane(task: RunTask) -> Do:
    yield run_task_in_pane(task)(task.details).nvim


@prog.do(Maybe[Pid])
def tmux_run_command(task: RunTask) -> Do:
    yield run_in_pane(task)


def tmux_can_run(task: RunTaskDetails) -> Boolean:
    return isinstance(task.details, (UiSystemTaskDetails, UiShellTaskDetails))


__all__ = ('tmux_run_command', 'tmux_can_run')
