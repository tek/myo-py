from typing import TypeVar, Generic

from amino import Dat, List, do, Do, Maybe, Boolean, L, _, Nil
from amino.dispatch import dispatch_alg
from amino.state import EitherState

from myo.ui.data.view import Layout
from myo.ui.data.space import Space
from myo.ui.data.window import Window
from myo.util import Ident
from myo.ui.data.tree import ViewTree, LayoutNode, PaneNode
from myo.ui.data.ui import UiData

A = TypeVar('A')


class ViewPath(Generic[A], Dat['ViewPath']):

    @staticmethod
    def cons(
        view: A,
        layouts: List[Layout],
        window: Window,
        space: Space,
    ) -> 'ViewPath':
        return ViewPath(
            view,
            layouts,
            window,
            space,
        )

    def __init__(self, view: A, layouts: List[Layout], window: Window, space: Space) -> None:
        self.view = view
        self.layouts = layouts
        self.window = window
        self.space = space


class PanePathView:

    def __init__(self, ident: Ident, stack: List[Layout], window: Window, space: Space) -> None:
        self.ident = ident
        self.stack = stack
        self.window = window
        self.space = space

    def recurse(self, layout: Layout, node: ViewTree) -> Maybe[ViewPath]:
        return pane_path_view(self.ident, node, self.stack.cons(layout), self.window, self.space)

    def layout_node(self, node: LayoutNode) -> Maybe[ViewPath]:
        return node.sub.find_map(L(self.recurse)(node.data, _))

    def pane_node(self, node: PaneNode) -> Maybe[ViewPath]:
        pane = node.data
        return Boolean(pane.ident == self.ident).m(lambda: ViewPath(pane, self.stack, self.window, self.space))


def pane_path_view(ident: Ident, view: ViewTree, stack: List[Layout], window: Window, space: Space) -> Maybe[ViewPath]:
    return dispatch_alg(PanePathView(ident, stack, window, space), ViewTree)(view)


def pane_path_space(ident: Ident, space: Space) -> Maybe[ViewPath]:
    return space.windows.find_map(lambda a: pane_path_view(ident, a.layout, Nil, a, space))


@do(EitherState[UiData, ViewPath])
def pane_path(ident: Ident) -> Do:
    spaces = yield EitherState.inspect(_.spaces)
    path_m = spaces.find_map(L(pane_path_space)(ident, _))
    yield EitherState.lift(path_m.to_either(f'pane not found: {ident}'))


__all__ = ('ViewPath', 'pane_path')
