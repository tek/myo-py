from chiasma.util.id import IdentSpec, ensure_ident_or_generate

from amino import do, Do
from amino.logging import module_log
from amino.state import EitherState

from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.pane import open_or_toggle_pane, map_window_trees
from myo.components.ui.compute.pane import render_view

log = module_log()


@do(EitherState[str, UiData, Window])
def ui_toggle_pane(ident: Ident) -> Do:
    yield map_window_trees(lambda a: open_or_toggle_pane(ident)(a).get_or_strict(a)).nvim


@prog.do(None)
def toggle_pane(ident_spec: IdentSpec) -> Do:
    ident = ensure_ident_or_generate(ident_spec)
    yield Ribo.lift_comp(ui_toggle_pane(ident), UiData)
    yield render_view(ident)


__all__ = ('toggle_pane',)
