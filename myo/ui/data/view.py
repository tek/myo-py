from chiasma.ui.view import UiPane, UiLayout, UiView
from chiasma.ui.state import ViewState
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.util.id import ensure_ident, IdentSpec

from amino import Boolean, ADT, Maybe, Path
from amino.tc.base import tc_prop

from myo.util import Ident


class View(ADT['View']):

    def __init__(self, ident: Ident, state: ViewState, geometry: ViewGeometry, ui: str) -> None:
        self.ident = ident
        self.state = state
        self.geometry = geometry
        self.ui = ui


class Layout(View):

    @staticmethod
    def cons(
            ident: IdentSpec=None,
            state: ViewState=None,
            geometry: ViewGeometry=None,
            ui: str='tmux',
            vertical: bool=True,
    ) -> 'Layout':
        return Layout(
            ensure_ident(ident),
            state or ViewState.cons(),
            geometry or ViewGeometry.cons(),
            ui,
            Boolean(vertical),
        )

    def __init__(
            self,
            ident: Ident,
            state: ViewState,
            geometry: ViewGeometry,
            ui: str,
            vertical: Boolean,
    ) -> None:
        super().__init__(ident, state, geometry, ui)
        self.vertical = vertical

    @property
    def vertical_str(self) -> str:
        return 'vertical' if self.vertical else 'horizontal'


class Pane(View):

    @staticmethod
    def cons(
            ident: IdentSpec=None,
            state: ViewState=None,
            geometry: ViewGeometry=None,
            ui: str='tmux',
            open: bool=False,
            cwd: Path=None,
    ) -> 'Pane':
        return Pane(
            ensure_ident(ident),
            state or ViewState.cons(),
            geometry or ViewGeometry.cons(),
            ui,
            Boolean(open),
            Maybe.optional(cwd),
        )

    def __init__(
            self,
            ident: Ident,
            state: ViewState,
            geometry: ViewGeometry,
            ui: str,
            open: Boolean,
            cwd: Maybe[Path],
    ) -> None:
        super().__init__(ident, state, geometry, ui)
        self.open = open
        self.cwd = cwd


class MyoUiPane(UiPane, tpe=Pane):

    @tc_prop
    def ident(self, a: Pane) -> Ident:
        return a.ident

    @tc_prop
    def open(self, a: Pane) -> Ident:
        return a.open

    def cwd(self, a: Pane) -> Maybe[Path]:
        return a.cwd


class MyoUiLayout(UiLayout, tpe=Layout):

    @tc_prop
    def ident(self, a: Pane) -> Ident:
        return a.ident


class MyoPaneUiView(UiView, tpe=Pane):

    def state(self, a: Pane) -> ViewState:
        return a.state

    def geometry(self, a: Pane) -> ViewGeometry:
        return a.geometry


class MyoLayoutUiView(UiView, tpe=Layout):

    def state(self, a: Layout) -> ViewState:
        return a.state

    def geometry(self, a: Layout) -> ViewGeometry:
        return a.geometry


__all__ = ('View', 'Layout', 'Pane', 'ViewGeometry')
