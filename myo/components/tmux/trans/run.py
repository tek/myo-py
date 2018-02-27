from amino import do, Do, Boolean
from amino.lenses.lens import lens
from amino.dispatch import PatMat

from chiasma.io.state import TS
from chiasma.data.tmux import TmuxData
from chiasma.pane import pane_by_ident
from chiasma.commands.pane import send_keys

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.trans.action import TransM

from myo.env import Env
from myo.command.run_task import RunTask, UiSystemTask, UiShellTask


class run_task_in_pane(PatMat, alg=RunTask):

    @do(TS)
    def ui_system_task(self, task: UiSystemTask) -> Do:
        print(task.pane)
        cmd = task.command
        pane = task.pane
        tpane = yield pane_by_ident(pane.ident).zoom(lens.comp)
        id = yield TS.from_maybe(tpane.id, f'no tmux id for pane {pane.ident}')
        yield TS.lift(send_keys(id, cmd.lines))

    @do(TS)
    def ui_shell_task(self, task: UiShellTask) -> Do:
        print(task.pane)
        cmd = task.command
        pane = task.pane
        tpane = yield pane_by_ident(pane.ident).zoom(lens.comp)
        id = yield TS.from_maybe(tpane.id, f'no tmux id for pane {pane.ident}')
        yield TS.lift(send_keys(id, cmd.lines))

    def patmat_default(self, task: RunTask) -> TS:
        pass


@trans.free.unit(trans.st)
@do(TS[ComponentData[Env, TmuxData], None])
def run_in_pane(task: RunTask) -> Do:
    yield run_task_in_pane.match(task)
    yield TS.pure(None)


@trans.free.do(trans.st)
@do(TransM)
def run_command(task: RunTask) -> Do:
    yield run_in_pane(task).m


def tmux_can_run(task: RunTask) -> Boolean:
    print(task)
    return isinstance(task, (UiSystemTask, UiShellTask))


__all__ = ('run_command', 'tmux_can_run')
