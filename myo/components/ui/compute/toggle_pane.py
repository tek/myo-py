from amino import do, Do

from chiasma.util.id import IdentSpec, ensure_ident
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.state import EitherState

from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.pane import ui_modify_pane
from myo.components.ui.compute.pane import render_pane

log = module_log()


@do(EitherState[UiData, Window])
def ui_toggle_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.state.minimized.modify(lambda a: ~a))


@prog.do
def toggle_pane(ident_spec: IdentSpec) -> Do:
    ident = ensure_ident(ident_spec)
    yield Ribo.lift_comp(ui_toggle_pane(ident).nvim, UiData)
    yield render_pane(ident)


__all__ = ('toggle_pane',)
