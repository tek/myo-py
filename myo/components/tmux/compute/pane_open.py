from amino import do, Do
from amino.lenses.lens import lens

from chiasma.commands.pane import window_pane_open
from chiasma.window.main import window_by_ident
from chiasma.pane import pane_by_ident
from chiasma.io.state import TS
from chiasma.io.compute import TmuxIO

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from myo.ui.data.window import Window
from myo.ui.data.view import Pane
from myo.components.tmux.tpe import TmuxRibosome


@prog
@do(NS[TmuxRibosome, bool])
def tmux_window_pane_open(window: Window, pane: Pane) -> Do:
    native_window = yield Ribo.zoom_comp(window_by_ident(window.ident).nvim.zoom(lens.views))
    native_pane = yield Ribo.zoom_comp(pane_by_ident(pane.ident).nvim.zoom(lens.views))
    yield TS.lift((native_window.id & native_pane.id).map2(window_pane_open).get_or(TmuxIO.pure, False)).nvim


__all__ = ('tmux_window_pane_open',)
