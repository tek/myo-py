from amino import do, Do, Boolean
from amino.boolean import true
from amino.lenses.lens import lens

from chiasma.io.state import TS
from chiasma.data.tmux import TmuxData
from chiasma.pane import pane_by_ident
from chiasma.commands.pane import send_keys

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData

from myo.data.command import Command
from myo.env import Env
from myo.ui.data.view import Pane


@trans.free.unit(trans.st)
@do(TS[ComponentData[Env, TmuxData], None])
def run_command(cmd: Command, pane: Pane) -> Do:
    tpane = yield pane_by_ident(pane.ident).zoom(lens.comp)
    id = yield TS.from_maybe(tpane.id, f'no tmux id for pane {pane.ident}')
    yield TS.lift(send_keys(id, cmd.lines))
    yield TS.pure(None)


def tmux_can_run(cmd: Command) -> Boolean:
    return true


__all__ = ('run_command', 'tmux_can_run')
