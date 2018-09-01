from uuid import uuid4

from amino import Dat, Maybe, Just, Either, Nothing
from amino.case import Case

from chiasma.data.view_tree import ViewTree, LayoutNode, PaneNode, SubUiNode
from chiasma.util.id import IdentSpec, ensure_ident_or_generate

from myo.util import Ident
from myo.ui.data.view import Pane, Layout


class Window(Dat['Window']):

    @staticmethod
    def cons(
            ident: IdentSpec=None,
            layout: LayoutNode[Layout, Pane]=None,
    ) -> 'Window':
        return Window(
            ensure_ident_or_generate(ident),
            layout or ViewTree.layout(),
        )

    def __init__(self, ident: Ident, layout: LayoutNode[Layout, Pane]) -> None:
        self.ident = ident
        self.layout = layout


class FindPrincipal(Case, alg=ViewTree):

    def layout_node(self, node: LayoutNode) -> Maybe[Pane]:
        return node.sub.find_map(self)

    def pane_node(self, node: PaneNode) -> Maybe[Pane]:
        return Just(node.data)

    def sub_ui_node(self, node: SubUiNode) -> Maybe[Pane]:
        return Nothing


def find_principal(window: Window) -> Either[str, Pane]:
    return FindPrincipal.match(window.layout).to_either(f'window contains no pane')


__all__ = ('Window', 'find_principal')
