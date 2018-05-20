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
from myo.components.ui.compute.pane import render_view
from myo.ui.data.view import Pane

log = module_log()


def open_or_toggle_minimized(pane: Pane) -> Pane:
    return (
        pane.set.open(True)
        if not pane.open else
        lens.state.minimized.modify(lambda a: ~a)(pane)
    )


@do(EitherState[UiData, Window])
def ui_toggle_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, open_or_toggle_minimized)


@prog.do
def toggle_pane(ident_spec: IdentSpec) -> Do:
    ident = ensure_ident(ident_spec)
    yield Ribo.lift_comp(ui_toggle_pane(ident).nvim, UiData)
    yield render_view(ident)


__all__ = ('toggle_pane',)
