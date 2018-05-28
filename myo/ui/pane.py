from typing import Tuple, Callable, TypeVar

from amino import do, Do, Either, Maybe, _, curried, L, List, Nothing, Just
from amino.state import EitherState, State
from amino.case import Case
from amino.logging import module_log
from amino.lenses.lens import lens
from amino.boolean import true
from chiasma.data.view_tree import (map_panes, ViewTree, find_in_view_tree, LayoutNode, map_layouts, map_layout_nodes,
                                    map_pane_nodes)
from chiasma.util.id import IdentSpec
from chiasma.open_pane import pane_open_layout_hook, mod_pane_open, pane_node_open
from chiasma.mod_pane import mod_pane

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view import Layout, Pane, has_ident
from myo.ui.data.view_tree import MyoViewTree, MyoLayoutNode, MyoPaneNode

A = TypeVar('A')
log = module_log()


def find_in_window(
        pred: Callable[[MyoViewTree], Maybe[A]],
        window: Window,
) -> Maybe[Tuple[Window, MyoViewTree]]:
    return find_in_view_tree(pane=pred, layout=pred)(window.layout).map(lambda pane: (window, pane))


def find_in_windows(
        pred: Callable[[MyoViewTree], Maybe[A]],
        space: Space,
) -> Maybe[Tuple[Space, Window, MyoViewTree]]:
    a = space.windows.find_map(L(find_in_window)(pred, _))
    return a.map2(lambda w, p: (space, w, p))


def find_in_spaces(pred: Callable[[MyoViewTree], Maybe[A]], spaces: List[Space]) -> None:
    return spaces.find_map(lambda a: find_in_windows(pred, a))


@do(State[UiData, Maybe[Tuple[Space, Window, MyoViewTree]]])
def find_in_ui(pred: Callable[[MyoViewTree], Maybe[A]]) -> Do:
    spaces = yield State.inspect(_.spaces)
    return find_in_spaces(pred, spaces)


spaces_layout_lens = lens.Each().windows.Each().layout
uidata_layout_lens = lens.spaces & spaces_layout_lens


def map_window_trees(mod: Callable[[MyoViewTree], MyoViewTree]) -> EitherState[UiData, None]:
    return EitherState.modify(uidata_layout_lens.modify(mod))


def ui_modify_layout_nodes(
        pred: Callable[[MyoLayoutNode], bool],
        mod: Callable[[MyoLayoutNode], MyoLayoutNode],
) -> EitherState[UiData, None]:
    return map_window_trees(map_layout_nodes(pred, mod))


def ui_modify_pane_nodes(
        pred: Callable[[Pane], bool],
        mod: Callable[[MyoPaneNode], MyoPaneNode],
) -> EitherState[UiData, None]:
    return map_window_trees(map_pane_nodes(pred, mod))


def ui_modify_layout_node(ident: Ident, mod: Callable[[MyoLayoutNode], MyoLayoutNode]) -> EitherState[UiData, Window]:
    return ui_modify_layout_nodes(lambda a: has_ident(ident)(a.data), mod)


def ui_modify_pane_node(ident: Ident, mod: Callable[[MyoPaneNode], MyoPaneNode]) -> EitherState[UiData, Window]:
    return ui_modify_pane_nodes(lambda a: has_ident(ident)(a.data), mod)


def ui_modify_layouts(pred: Callable[[Layout], bool], mod: Callable[[Layout], Layout]) -> EitherState[UiData, None]:
    return map_window_trees(map_layouts(pred, mod))


def ui_modify_panes(pred: Callable[[Pane], bool], mod: Callable[[Pane], Pane]) -> EitherState[UiData, None]:
    return map_window_trees(map_panes(pred, mod))


def ui_modify_layout(ident: Ident, mod: Callable[[Layout], Layout]) -> EitherState[UiData, Window]:
    return ui_modify_layouts(has_ident(ident), mod)


def ui_modify_pane(ident: Ident, mod: Callable[[Pane], Pane]) -> EitherState[UiData, Window]:
    return ui_modify_panes(has_ident(ident), mod)


def map_panes_in_spaces(
        pred: Callable[[Pane], bool],
        update: Callable[[Pane], Pane],
) -> List[Space]:
    return spaces_layout_lens.modify(map_panes(pred, update))


class insert_pane(Case, alg=ViewTree):

    def __init__(self, pane: Pane, layout: Ident) -> None:
        self.pane = pane
        self.layout = layout

    def layout_node(self, node: LayoutNode) -> Maybe[ViewTree]:
        return (
            Just(node.append1.sub(ViewTree.pane(self.pane)))
            if node.data.ident == self.layout else
            node.sub.find_map(self) / node.replace_sub
        )

    def case_default(self, node: ViewTree) -> Maybe[ViewTree]:
        return Nothing


@curried
def insert_pane_into_window(pane: Pane, layout: Ident, window: Window) -> Maybe[Window]:
    return insert_pane(pane, layout)(window.layout) / window.set.layout


@curried
def insert_pane_into_space(pane: Pane, layout: Ident, space: Space) -> Maybe[Space]:
    return space.windows.find_map(insert_pane_into_window(pane, layout)) / space.replace_window


@curried
def insert_pane_into_ui(pane: Pane, layout: Ident, ui: UiData) -> Either[str, UiData]:
    return (
        ui.spaces.find_map(insert_pane_into_space(pane, layout))
        .map(ui.replace_space)
        .to_either(lambda: f'no layout with ident {layout}')
    )


def open_or_toggle_minimized(node: MyoPaneNode) -> MyoPaneNode:
    l = (
        lens.data.state.minimized.modify(lambda a: ~a)
        if node.data.open else
        pane_node_open.set(true)
    )
    return l(node)


def open_or_toggle_pane(spec: IdentSpec) -> Callable[[MyoViewTree], Either[str, MyoViewTree]]:
    return mod_pane(mod_pane_open(spec, open_or_toggle_minimized), pane_open_layout_hook)


__all__ = ('find_in_window', 'find_in_windows', 'find_in_ui', 'ui_modify_pane', 'insert_pane_into_ui',
           'ui_modify_layout',)
