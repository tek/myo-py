from amino import do, Do
from amino.lenses.lens import lens

from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import Ident
from chiasma.pane import pane_by_ident

from myo.components.tmux.tpe import TmuxRibosome


@do(NS[TmuxRibosome, int])
def pane_id_by_ident(ident: Ident) -> Do:
    pane = yield Ribo.zoom_comp(pane_by_ident(ident).nvim.zoom(lens.views))
    yield NS.m(pane.id, lambda: f'pane `{ident}` has no id')


__all__ = ('pane_id_by_ident',)
