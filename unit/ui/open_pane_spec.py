from typing import TypeVar

from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from chiasma.data.view_tree import ViewTree
from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.tmux import TmuxData
from chiasma.data.window import Window as TWindow
from chiasma.render import render
from chiasma.data.session import Session
from chiasma.io.state import TS
from chiasma.commands.pane import all_panes, PaneData
from chiasma.util.id import IdentSpec, ensure_ident, StrIdent

from amino import List, do, Do, Dat
from amino.lenses.lens import lens
from amino.boolean import false

from myo.ui.data.ui_data import UiData
from myo.ui.data.view import Layout, Pane, ViewGeometry
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.ui.data.view_path import pane_path
from myo.components.ui.compute.open_pane import ui_open_pane

D = TypeVar('D')


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
def open_pane(ident_spec: IdentSpec) -> Do:
    ident = ensure_ident(ident_spec)
    yield ui_open_pane(ident).transform_s_lens(lens.ui).tmux
    a = yield pane_path(ident).transform_s_lens(lens.ui).tmux
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
            return ui_open_pane(StrIdent(name)).transform_s_lens(lens.ui).tmux
        @do(TS[OPData, None])
        def go() -> Do:
            yield ui_open('one')
            yield ui_open('two')
            yield ui_open('three')
            yield ui_open('four')
            yield open_pane('five')
            yield all_panes().state
        s, panes = self.run(go(), data)
        return k(panes).must(have_length(5))


__all__ = ('OpenPaneSpec',)
