from chiasma.io.state import TS
from chiasma.util.id import Ident
from chiasma.commands.pane import select_pane

from amino import do, Do

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS

from myo.components.tmux.tpe import TmuxRibosome
from myo.components.tmux.pane import pane_id_by_ident


@prog
@do(NS[TmuxRibosome, None])
def tmux_focus_pane(ident: Ident) -> Do:
    id = yield pane_id_by_ident(ident)
    yield TS.lift(select_pane(id)).nvim


__all__ = ('tmux_focus_pane',)
