from typing import Tuple, TypeVar

from kallikrein import k, Expectation

from chiasma.data.view_tree import map_nodes, ViewTree
from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.tmux import TmuxData
from chiasma.data.window import Window as TWindow
from chiasma.render import render
from chiasma.data.session import Session
from chiasma.io.state import TS
from chiasma.commands.pane import all_panes, PaneData

from amino import List, do, Do, Dat, Either, Right, Boolean
from amino.state import EitherState
from amino.lenses.lens import lens
from amino.boolean import true, false

from myo.ui.data.ui_data import UiData
from myo.ui.data.view import Layout, Pane, ViewGeometry
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view_path import pane_path

D = TypeVar('D')


@do(EitherState[UiData, Window])
def ui_open_pane(name: str) -> Do:
    @do(Either[str, Window])
    def find_pane(window: Window) -> Do:
        new = yield map_nodes(lambda a: Boolean(a.data.ident == name), lens.data.open.set(true))(window.layout)
        yield Right(window.copy(layout=new))
    @do(Either[str, Tuple[Space, Window]])
    def find_window(space: Space) -> Do:
        win = yield space.windows.find_map_e(find_pane)
        yield Right((space.replace_window(win), win))
    @do(Either[str, Tuple[UiData, Window]])
    def find_space(ui: UiData) -> Do:
        new, window = yield ui.spaces.find_map_e(find_window).lmap(lambda err: f'pane not found: {name}')
        yield Right((ui.replace_space(new), window))
    data, window = yield EitherState.inspect_f(find_space)
    yield EitherState.set(data)
    yield EitherState.pure(window)


class OPData(Dat['OPData']):

    @staticmethod
    def cons(layout: ViewTree) -> 'OPData':
        ws = List(Window.cons('main', layout=layout))
        spaces = List(Space.cons('main', ws))
        ui = UiData(spaces)
        tm = TmuxData.cons(sessions=List(Session.cons('main', id=0)), windows=List(TWindow.cons('main', id=0)))
        return OPData(ui, tm)

    def __init__(self, ui: UiData, tmux: TmuxData) -> None:
        self.ui = ui
        self.tmux = tmux


@do(TS[OPData, None])
def open_pane(name: str) -> Do:
    yield ui_open_pane(name).transform_s_lens(lens.ui).tmux
    a = yield pane_path(name).transform_s_lens(lens.ui).tmux
    yield render(P=Pane, L=Layout)(a.space.ident, a.window.ident, a.window.layout).transform_s_lens(lens.tmux)


class OpenPaneSpec(TmuxSpec):
    '''
    four nested layouts $four
    '''

    def four(self) -> Expectation:
        layout = ViewTree.layout(
            Layout.cons('root'),
            List(
                ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(min_size=30))),
                ViewTree.layout(
                    Layout.cons('main', vertical=false),
                    List(
                        ViewTree.pane(Pane.cons('two')),
                        ViewTree.layout(
                            Layout.cons('sub1'),
                            List(
                                ViewTree.pane(Pane.cons('three')),
                                ViewTree.layout(
                                    Layout.cons('sub2', vertical=false),
                                    List(
                                        ViewTree.pane(Pane.cons('four')),
                                        ViewTree.pane(Pane.cons('five')),
                                    )
                                )
                            )
                        )
                    )
                ),
            )
        )
        data = OPData.cons(layout)
        def ui_open(name: str) -> TS[OPData, None]:
            return ui_open_pane(name).transform_s_lens(lens.ui).tmux
        @do(TS[OPData, None])
        def go() -> Do:
            yield ui_open('one')
            yield ui_open('two')
            yield ui_open('three')
            yield ui_open('four')
            yield open_pane('five')
            yield all_panes().state
        s, panes = self.run(go(), data)
        target = List(
            PaneData(0, 301, 59, 0),
            PaneData(4, 150, 30, 60),
            PaneData(3, 150, 2, 60),
            PaneData(2, 75, 27, 63),
            PaneData(1, 74, 27, 63),
        )
        return k(panes) == target


__all__ = ('OpenPaneSpec',)
