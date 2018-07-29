from typing import Tuple

from amino import do, Do, Just, Nothing, List, Nil

from chiasma.util.id import IdentSpec
from chiasma.data.view_tree import find_in_view_tree, ViewTree, SubUiNode
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.state import EitherState
from amino.case import Case

from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.components.ui.compute.pane import render_view
from myo.ui.data.view import Layout, Pane
from myo.ui.pane import ui_modify_layout_node
from myo.ui.data.view_tree import MyoLayoutNode, MyoViewTree, MyoPaneNode
from myo.util.id import ensure_ident_prog

log = module_log()


class open_first_pane(Case[MyoViewTree, Tuple[MyoViewTree, bool]], alg=ViewTree):

    def layout(self, node: MyoLayoutNode) -> Tuple[MyoViewTree, bool]:
        def folder(z: Tuple[List[MyoViewTree], bool], a: MyoViewTree) -> Tuple[MyoViewTree, bool]:
            old, found_pre = z
            new, found_post = (
                (a, True)
                if found_pre else
                self(a)
            )
            return old.cat(new), found_post
        new, found = node.sub.fold_left((Nil, False))(folder)
        v = node.set.sub(new)
        return v, found

    def pane(self, a: MyoPaneNode) -> Tuple[MyoViewTree, bool]:
        return lens.data.open.set(True)(a), True

    def sub_ui(self, a: SubUiNode[Layout, Pane]) -> Tuple[MyoViewTree, bool]:
        return a, False


def layout_open(node: MyoLayoutNode) -> MyoLayoutNode:
    return find_in_view_tree(pane=lambda a: Just(True) if a.data.open else Nothing)(node).present


def open_layout(node: MyoLayoutNode) -> MyoLayoutNode:
    new, found = open_first_pane.match(node)
    return new


def open_or_toggle_minimized(node: MyoLayoutNode) -> MyoLayoutNode:
    return (
        lens.data.state.minimized.modify(lambda a: ~a)(node)
        if layout_open(node) else
        open_layout(node)
    )


@do(EitherState[str, UiData, Window])
def ui_toggle_layout(ident: Ident) -> Do:
    yield ui_modify_layout_node(ident, open_or_toggle_minimized)
    # yield map_window_trees(lambda a: open_or_toggle_layout(ident)(a).get_or_strict(a)).nvim


@prog.do(None)
def toggle_layout(ident_spec: IdentSpec) -> Do:
    ident = yield ensure_ident_prog(ident_spec)
    yield Ribo.lift_comp(ui_toggle_layout(ident).nvim, UiData)
    yield render_view(ident)


__all__ = ('toggle_layout',)
