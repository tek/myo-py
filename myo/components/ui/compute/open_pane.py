from amino import do, Do, Dat

from chiasma.util.id import IdentSpec, ensure_ident
from chiasma.open_pane import ui_open_pane
from amino.logging import module_log

from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.io.state import NS

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.pane import map_window_trees
from myo.components.ui.compute.pane import render_view

log = module_log()


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(self) -> None:
        pass


@do(NS[UiData, None])
def chiasma_open_pane(ident: Ident) -> Do:
    yield map_window_trees(lambda a: ui_open_pane(ident)(a).get_or_strict(a)).nvim


@prog.do(None)
def open_pane(ident_spec: IdentSpec, options: OpenPaneOptions) -> Do:
    ident = ensure_ident(ident_spec)
    yield Ribo.lift_comp(chiasma_open_pane(ident), UiData)
    yield render_view(ident)


__all__ = ('open_pane',)
