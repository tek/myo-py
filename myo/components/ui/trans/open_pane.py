from amino import do, Do, Dat
from amino.boolean import true

from chiasma.util.id import IdentSpec, ensure_ident
from amino.state import EitherState
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.trans.action import Trans

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.env import Env
from myo.ui.pane import ui_modify_pane
from myo.components.ui.trans.pane import render_pane


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(
            self,
    ) -> None:
        pass


@do(EitherState[UiData, Window])
def ui_open_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.open.set(true))


@trans.free.result(trans.st)
@do(EitherState[ComponentData[Env, UiData], Window])
def ui_open_pane_trans(ident_spec: IdentSpec) -> Do:
    ident = ensure_ident(ident_spec)
    yield ui_open_pane(ident).transform_s_lens(lens.comp)


@trans.free.do()
@do(Trans[None])
def open_pane(ident_spec: IdentSpec, options: OpenPaneOptions) -> Do:
    ident = ensure_ident(ident_spec)
    yield ui_open_pane_trans(ident)
    yield render_pane(ident)


__all__ = ('open_pane',)
