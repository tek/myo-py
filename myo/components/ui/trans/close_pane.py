from amino import do, Do
from amino.state import EitherState
from amino.lenses.lens import lens
from amino.boolean import false

from chiasma.util.id import Ident

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.trans.action import TransM

from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.pane import ui_modify_pane
from myo.env import Env
from myo.components.ui.trans.pane import render_pane


@do(EitherState[UiData, Window])
def ui_close_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.data.open.set(false))


@trans.free.result(trans.st)
@do(EitherState[ComponentData[Env, UiData], Window])
def ui_close_pane_trans(ident: Ident) -> Do:
    yield ui_close_pane(ident).transform_s_lens(lens.comp)


@trans.free.do()
@do(TransM[None])
def close_pane(ident: Ident) -> Do:
    yield ui_close_pane_trans(ident).m
    yield render_pane(ident).m


__all__ = ('close_pane',)
