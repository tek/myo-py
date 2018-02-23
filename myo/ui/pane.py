from typing import Tuple, Callable, TypeVar

from amino import do, Do, Either, Boolean, Right, Maybe, _, curried, L
from amino.state import EitherState, State

from chiasma.data.view_tree import map_nodes, ViewTree, find_in_view_tree

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view import Layout, Pane

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
def ui_modify_pane(ident: Ident, mod: Callable[[Pane], Pane]) -> Do:
    @do(Either[str, Window])
    def find_pane(window: Window) -> Do:
        new = yield map_nodes(lambda a: Boolean(a.data.ident == ident), mod)(window.layout)
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


__all__ = ('find_in_window', 'find_in_windows', 'find_in_spaces', 'ui_modify_pane')
