from amino import do, Do
from amino.boolean import true
from amino.state import EitherState
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.env import Env
from myo.ui.pane import ui_modify_pane
from myo.components.ui.trans.pane import render_pane


@do(EitherState[UiData, Window])
def ui_minimize_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.state.minimized.set(true))


@trans.free.result(trans.st)
@do(EitherState[ComponentData[Env, UiData], Window])
def ui_minimize_pane_trans(ident: Ident) -> Do:
    yield ui_minimize_pane(ident).transform_s_lens(lens.comp)


@trans.free.do()
@do(TransM[None])
def minimize_pane(ident: Ident) -> Do:
    yield ui_minimize_pane_trans(ident).m
    yield render_pane(ident).m


__all__ = ('minimize_pane',)
