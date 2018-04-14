from numbers import Number

from amino import do, Do, List, Nil, _, Maybe
from amino.case import Case

from chiasma.data.view_tree import ViewTree, LayoutNode, PaneNode, SubUiNode
from chiasma.ui.view_geometry import ViewGeometry

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.config.component import ComponentData

from myo.env import Env
from myo.ui.data.ui_data import UiData
from myo.data.info import InfoWidget
from myo.ui.data.space import Space
from myo.ui.data.window import Window
from myo.ui.data.view import Layout, Pane


def format_geometry(geo: ViewGeometry) -> str:
    def field(key: str, value: Maybe[Number]) -> Maybe[str]:
        return value.map(lambda v: f'⚬{key} {v}')
    fields = geo._dat__items.flat_map2(field)
    return fields.join_tokens


class format_layout(Case, alg=ViewTree):

    def layout_node(self, node: LayoutNode[Layout, Pane]) -> List[str]:
        direction = '▤' if node.data.vertical else '▥'
        desc = f'{direction} {node.data.ident.str}'
        return (node.sub // self).indent(1).cons(desc)

    def pane_node(self, node: PaneNode[Layout, Pane]) -> List[str]:
        return List(f'◳ {node.data.ident.str} {format_geometry(node.data.geometry)}')

    def sub_ui_node(self, node: SubUiNode[Layout, Pane]) -> List[str]:
        return Nil


def format_window(window: Window) -> List[str]:
    desc = f'□ {window.ident.str}'
    return format_layout.match(window.layout).indent(1).cons(desc)


def format_space(space: Space) -> List[str]:
    desc = f'⬚ {space.ident.str}'
    return (space.windows // format_window).indent(1).cons(desc)


@prog
@do(NS[ComponentData[Env, UiData], InfoWidget])
def ui_info() -> Do:
    spaces = yield NS.inspect(_.comp.spaces)
    tree = spaces // format_space
    yield NS.pure(InfoWidget(List('Ui:') + tree.indent(1)))


__all__ = ('ui_info',)
