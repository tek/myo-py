from amino import do, Do, Dat, Maybe, List
from amino.boolean import true
from amino.state import EitherState
from amino.lenses.lens import lens
from amino.dispatch import PatMat

from chiasma.data.view_tree import ViewTree, LayoutNode, PaneNode, SubUiNode

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.data.view import Layout, Pane
from myo.env import Env
from myo.ui.ui import Ui
from myo.ui.pane import ui_modify_pane
from myo.components.ui.trans.pane import render_pane


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(
            self,
    ) -> None:
        pass


@do(EitherState[UiData, Window])
def ui_open_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.data.open.set(true))


class collect_uis(PatMat, alg=ViewTree):

    def __init__(self, current: Maybe[Ui], all: List[Ui]) -> None:
        self.current = current
        self.all = all

    def layout_node(self, node: LayoutNode[Layout, Pane]) -> Do:
        pass

    def pane_node(self, node: PaneNode[Layout, Pane]) -> Do:
        pass

    def sub_ui_node(self, node: SubUiNode[Layout, Pane]) -> Do:
        pass


@trans.free.result(trans.st)
@do(EitherState[ComponentData[Env, UiData], Window])
def ui_open_pane_trans(ident: Ident) -> Do:
    yield ui_open_pane(ident).transform_s_lens(lens.comp)


@trans.free.do()
@do(TransM[None])
def open_pane(ident: Ident, options: OpenPaneOptions) -> Do:
    yield ui_open_pane_trans(ident).m
    yield render_pane(ident).m


__all__ = ('open_pane',)
