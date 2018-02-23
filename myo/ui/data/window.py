from uuid import uuid4

from amino import Dat, Maybe, Just, Either, Nothing
from amino.dispatch import PatMat

from chiasma.data.view_tree import ViewTree, LayoutNode, PaneNode, SubUiNode

from myo.util import Ident
from myo.ui.data.view import Pane


class Window(Dat['Window']):

    @staticmethod
    def cons(
            ident: Ident=None,
            name: str=None,
            layout: LayoutNode=None,
    ) -> 'Window':
        id = ident or uuid4()
        return Window(
            id,
            name or id,
            layout or ViewTree.layout(),
        )

    def __init__(self, ident: Ident, name: str, layout: LayoutNode) -> None:
        self.ident = ident
        self.name = name
        self.layout = layout


class FindPrincipal(PatMat, alg=ViewTree):

    def layout_node(self, node: LayoutNode) -> Maybe[Pane]:
        return node.sub.find_map(self)

    def pane_node(self, node: PaneNode) -> Maybe[Pane]:
        return Just(node.data)

    def sub_ui_node(self, node: SubUiNode) -> Maybe[Pane]:
        return Nothing


def find_principal(window: Window) -> Either[str, Pane]:
    return FindPrincipal.match(window.layout).to_either(f'window contains no pane')


__all__ = ('Window', 'find_principal')
