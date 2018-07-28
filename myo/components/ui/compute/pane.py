from typing import Tuple, Callable

from amino import do, Do, curried, Maybe, Just, Nothing, _

from chiasma.data.view_tree import ViewTree
from amino.state import State
from amino.lenses.lens import lens
from amino.util.tuple import lift_tuple

from ribosome.compute.api import prog
from ribosome.compute.program import Program
from ribosome.config.component import ComponentData
from ribosome.data.plugin_state import PluginState
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.io.state import NS
from ribosome.compute.prog import Prog

from myo.util import Ident
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view import Pane, Layout, has_ident
from myo.ui.pane import find_in_ui
from myo.env import Env
from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData
from myo.ui.data.view_tree import MyoViewTree
from myo.ui.ui import Ui


@curried
def match_ident(ident: Ident, node: MyoViewTree) -> Maybe[MyoViewTree]:
    return Just(node) if has_ident(ident)(node.data) else Nothing


@do(State[UiData, Maybe[Tuple[Space, Window, ViewTree[Layout, Pane]]]])
def view_path_by_ident(ident: Ident) -> Do:
    yield find_in_ui(match_ident(ident))


@prog
@do(State[PluginState[Env, MyoComponent], Program])
def config_uis() -> Do:
    components = yield State.inspect(_.components.all)
    yield State.pure(components // _.config // _.ui)


@prog.do(Tuple[Space, Window, Ui])
def view_owners(ident: Ident) -> Do:
    view_path_m = yield Ribo.lift_comp(view_path_by_ident(ident).nvim, UiData)
    space, window, view = yield Prog.from_maybe(view_path_m, f'no view with ident `{ident}`')
    uis = yield config_uis()
    owns_handlers = uis / _.owns_view
    owns = yield owns_handlers.traverse(lambda a: a(view.data), Prog)
    owners = uis.zip(owns).filter2(lambda a, b: b).flat_map(lift_tuple(0))
    owner = yield (
        Prog.from_maybe(owners.head, f'no owner for view {ident}')
        if owners.length <= 1
        else Prog.error('multiple owners for view {ident}')
    )
    yield Prog.pure((space, window, owner))


@prog.do(Program)
def view_prog(ident: Ident, prog: Callable[[Ui], Maybe[Program]], desc: str) -> Do:
    space, window, owner = yield view_owners(ident)
    yield Prog.m(prog(owner), lambda: '{type(owner)} has no handler for `{desc}`')


@prog.do(None)
def render_view(ident: Ident) -> Do:
    space, window, owner = yield view_owners(ident)
    renderer = yield Prog.from_maybe(owner.render, f'no renderer for {owner}')
    yield renderer(space.ident, window.ident, window.layout)


@prog
@do(NS[ComponentData[Env, UiData], Pane])
def ui_pane_by_ident(ident: Ident) -> Do:
    result = yield view_path_by_ident(ident).nvim.zoom(lens.comp)
    pane = (
        result
        .to_either(f'no pane for `{ident}`')
        .flat_map(lift_tuple(2))
        .map(_.data)
        .to_either(f'invalid result from `pane_path_by_ident`')
    )
    yield NS.e(pane)


__all__ = ('config_uis', 'pane_owners', 'render_pane', 'view_prog',)
