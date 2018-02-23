from typing import Tuple, Callable, TypeVar

from amino import do, Do, Dat, Either, Boolean, Right, Nothing, Maybe, List, _, curried, Just, L
from amino.boolean import true, false
from amino.state import EitherState, State
from amino.lenses.lens import lens
from amino.dispatch import PatMat

from chiasma.data.view_tree import map_nodes, ViewTree, LayoutNode, PaneNode, SubUiNode, find_in_view_tree

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome.plugin_state import PluginState
from ribosome.trans.handler import TransHandler
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view import Layout, Pane
from myo.config.component import MyoComponent
from myo.env import Env
from myo.ui.ui import Ui
from myo.settings import MyoSettings


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(
            self,
    ) -> None:
        pass


A = TypeVar('A')


def find_in_window(
        pred: Callable[[ViewTree[Layout, Pane]], Maybe[A]],
        window: Window,
) -> Maybe[Tuple[Window, ViewTree[Layout, Pane]]]:
    return find_in_view_tree(pane=pred)(window.layout).map(lambda pane: (window, pane))


def find_in_windows(
        pred: Callable[[ViewTree[Layout, Pane]], Maybe[A]],
        space: Space,
) -> Maybe[Tuple[Space, Window, ViewTree[Layout, Pane]]]:
    return space.windows.find_map(L(find_in_window)(pred, _)).map2(lambda w, p: (space, w, p))


@do(State[UiData, Maybe[Tuple[Space, Window, ViewTree[Layout, Pane]]]])
def find_in_spaces(pred: Callable[[ViewTree[Layout, Pane]], Maybe[A]]) -> Do:
    spaces = yield State.inspect(_.spaces)
    yield State.pure(spaces.find_map(curried(find_in_windows)(pred)))


@do(EitherState[UiData, Window])
def ui_open_pane(ident: Ident) -> Do:
    @do(Either[str, Window])
    def find_pane(window: Window) -> Do:
        new = yield map_nodes(lambda a: Boolean(a.data.ident == ident), lens.data.open.set(true))(window.layout)
        yield Right(window.copy(layout=new))
    @do(Either[str, Tuple[Space, Window]])
    def find_window(space: Space) -> Do:
        win = yield space.windows.find_map_e(find_pane)
        yield Right((space.replace_window(win), win))
    @do(Either[str, Tuple[UiData, Window]])
    def find_space(ui: UiData) -> Do:
        new, window = yield ui.spaces.find_map_e(find_window).lmap(lambda err: f'pane not found: {ident}')
        yield Right((ui.replace_space(new), window))
    data, window = yield EitherState.inspect_f(find_space)
    yield EitherState.set(data)
    yield EitherState.pure(window)


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
def ui_open_pane_trans(ident: Ident, options: OpenPaneOptions) -> Do:
    yield ui_open_pane(ident).transform_s_lens(lens.comp)


@trans.free.result(trans.st, component=false)
@do(State[PluginState[MyoSettings, Env, MyoComponent], TransHandler])
def config_uis() -> Do:
    components = yield State.inspect(_.components.all)
    yield State.pure(components // _.config // _.ui)


@curried
def has_ident(ident: Ident, node: PaneNode[Layout, Pane]) -> Boolean:
    return node.data.ident == ident


@curried
def match_ident(ident: Ident, node: PaneNode[Layout, Pane]) -> Maybe[PaneNode[Layout, Pane]]:
    return Just(node) if node.data.ident == ident else Nothing


@trans.free.result(trans.st)
@do(State[ComponentData, Pane])
def pane_path_by_ident(ident: Ident) -> Do:
    yield find_in_spaces(match_ident(ident)).transform_s_lens(lens.comp)


@trans.free.do()
@do(TransM)
def open_pane(ident: Ident, options: OpenPaneOptions) -> Do:
    pane_path_m = yield pane_path_by_ident(ident).m
    space, window, pane = yield TransM.from_maybe(pane_path_m, f'no pane with ident `{ident}`')
    uis = yield config_uis().m
    owns_handlers = uis / _.owns_pane
    owns = yield owns_handlers.traverse(lambda a: a(pane.data).m, TransM)
    owners = uis.zip(owns).filter2(lambda a, b: b).map(_[0])
    owner = yield (
        TransM.from_maybe(owners.head, f'no owner for pane {ident}')
        if owners.length <= 1
        else TransM.error('multiple owners for pane {ident}')
    )
    window1 = yield ui_open_pane_trans(ident, options).m
    renderer = yield TransM.from_maybe(owner.render, f'no renderer for {owner}')
    yield renderer(space.ident, window.ident, window1.layout).switch


__all__ = ('open_pane',)
