from typing import Tuple

from amino import do, Do, curried, Boolean, Maybe, Just, Nothing, _

from chiasma.data.view_tree import PaneNode, ViewTree
from amino.state import State, EitherState
from amino.lenses.lens import lens
from amino.boolean import false
from amino.util.tuple import lift_tuple

from ribosome.trans.api import trans
from ribosome.trans.action import TransM
from ribosome.dispatch.component import ComponentData
from ribosome.plugin_state import PluginState
from ribosome.trans.handler import TransHandler

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


@do(State[ComponentData[Env, UiData], Maybe[Tuple[Space, Window, ViewTree[Layout, Pane]]]])
def pane_path_by_ident(ident: Ident) -> Do:
    yield find_in_spaces(match_ident(ident)).zoom(lens.comp)


@trans.free.result(trans.st, component=false)
@do(State[PluginState[MyoSettings, Env, MyoComponent], TransHandler])
def config_uis() -> Do:
    components = yield State.inspect(_.components.all)
    yield State.pure(components // _.config // _.ui)


@trans.free.do()
@do(TransM[Tuple[Space, Window, Ui]])
def pane_owners(ident: Ident) -> Do:
    pane_path_m = yield pane_path_by_ident(ident).trans
    space, window, pane = yield TransM.from_maybe(pane_path_m, f'no pane with ident `{ident}`')
    uis = yield config_uis().m
    owns_handlers = uis / _.owns_pane
    owns = yield owns_handlers.traverse(lambda a: a(pane.data).m, TransM)
    owners = uis.zip(owns).filter2(lambda a, b: b).flat_map(lift_tuple(0))
    owner = yield (
        TransM.from_maybe(owners.head, f'no owner for pane {ident}')
        if owners.length <= 1
        else TransM.error('multiple owners for pane {ident}')
    )
    yield TransM.pure((space, window, owner))


@trans.free.do()
@do(TransM[None])
def render_pane(ident: Ident) -> Do:
    space, window, owner = yield pane_owners(ident).m
    renderer = yield TransM.from_maybe(owner.render, f'no renderer for {owner}')
    yield renderer(space.ident, window.ident, window.layout).m


@trans.free.result(trans.st)
@do(EitherState[ComponentData[Env, UiData], Pane])
def ui_pane_by_ident(ident: Ident) -> Do:
    result = yield pane_path_by_ident(ident).to(EitherState)
    pane = (
        result
        .to_either(f'no pane for `{ident}`')
        .flat_map(lift_tuple(2))
        .map(_.data)
        .to_either(f'invalid result from `pane_path_by_ident`')
    )
    yield EitherState.lift(pane)


__all__ = ('config_uis', 'pane_owners', 'render_pane')
