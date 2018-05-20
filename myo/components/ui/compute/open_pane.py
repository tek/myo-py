from amino import do, Do, Dat
from amino.boolean import true

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

log = module_log()


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(self) -> None:
        pass


@do(EitherState[UiData, Window])
def ui_open_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.open.set(true))


@prog.do
def open_pane(ident_spec: IdentSpec, options: OpenPaneOptions) -> Do:
    ident = ensure_ident(ident_spec)
    yield Ribo.lift_comp(ui_open_pane(ident).nvim, UiData)
    yield render_view(ident)


__all__ = ('open_pane',)
