from typing import Tuple

from amino import do, Do, curried, Boolean, Maybe, Just, Nothing, _

from chiasma.data.view_tree import PaneNode, ViewTree
from amino.state import State, EitherState
from amino.lenses.lens import lens
from amino.boolean import false
from amino.util.tuple import lift_tuple

from ribosome.compute.api import prog
from ribosome.compute.prog import Program, Prog
from ribosome.config.component import ComponentData
from ribosome.data.plugin_state import PluginState
from ribosome.compute.prog import Program, Prog
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.io.state import NS

from myo.util import Ident
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.ui import Ui
from myo.ui.data.view import Pane, Layout
from myo.ui.pane import find_in_spaces
from myo.settings import MyoSettings
from myo.env import Env
from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData


@curried
def has_ident(ident: Ident, node: PaneNode[Layout, Pane]) -> Boolean:
    return node.data.ident == ident


@curried
def match_ident(ident: Ident, node: PaneNode[Layout, Pane]) -> Maybe[PaneNode[Layout, Pane]]:
    return Just(node) if node.data.ident == ident else Nothing


@do(State[UiData, Maybe[Tuple[Space, Window, ViewTree[Layout, Pane]]]])
def pane_path_by_ident(ident: Ident) -> Do:
    yield find_in_spaces(match_ident(ident))


@prog
@do(State[PluginState[MyoSettings, Env, MyoComponent], Program])
def config_uis() -> Do:
    components = yield State.inspect(_.components.all)
    yield State.pure(components // _.config // _.ui)


@prog.do
@do(Prog[Tuple[Space, Window, Ui]])
def pane_owners(ident: Ident) -> Do:
    pane_path_m = yield Ribo.lift_comp(pane_path_by_ident(ident).nvim, UiData)
    space, window, pane = yield Prog.from_maybe(pane_path_m, f'no pane with ident `{ident}`')
    uis = yield config_uis()
    owns_handlers = uis / _.owns_pane
    owns = yield owns_handlers.traverse(lambda a: a(pane.data), Prog)
    owners = uis.zip(owns).filter2(lambda a, b: b).flat_map(lift_tuple(0))
    owner = yield (
        Prog.from_maybe(owners.head, f'no owner for pane {ident}')
        if owners.length <= 1
        else Prog.error('multiple owners for pane {ident}')
    )
    yield Prog.pure((space, window, owner))


@prog.do
@do(Prog[None])
def render_pane(ident: Ident) -> Do:
    space, window, owner = yield pane_owners(ident)
    renderer = yield Prog.from_maybe(owner.render, f'no renderer for {owner}')
    yield renderer(space.ident, window.ident, window.layout)


@prog
@do(NS[ComponentData[Env, UiData], Pane])
def ui_pane_by_ident(ident: Ident) -> Do:
    result = yield pane_path_by_ident(ident).nvim.zoom(lens.comp)
    pane = (
        result
        .to_either(f'no pane for `{ident}`')
        .flat_map(lift_tuple(2))
        .map(_.data)
        .to_either(f'invalid result from `pane_path_by_ident`')
    )
    yield NS.lift(pane)


__all__ = ('config_uis', 'pane_owners', 'render_pane')
