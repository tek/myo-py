from typing import Callable

from chiasma.ui.view import UiPane, UiLayout, UiView
from chiasma.ui.state import ViewState
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.util.id import ensure_ident_or_generate, IdentSpec

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
            ensure_ident_or_generate(ident),
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
            pin: bool=False,
    ) -> 'Pane':
        return Pane(
            ensure_ident_or_generate(ident),
            state or ViewState.cons(),
            geometry or ViewGeometry.cons(),
            ui,
            Boolean(open),
            Maybe.optional(cwd),
            Boolean(pin),
        )

    def __init__(
            self,
            ident: Ident,
            state: ViewState,
            geometry: ViewGeometry,
            ui: str,
            open: Boolean,
            cwd: Maybe[Path],
            pin: Boolean,
    ) -> None:
        super().__init__(ident, state, geometry, ui)
        self.open = open
        self.cwd = cwd
        self.pin = pin


class MyoUiPane(UiPane, tpe=Pane):

    @tc_prop
    def ident(self, a: Pane) -> Ident:
        return a.ident

    @tc_prop
    def open(self, a: Pane) -> Ident:
        return a.open

    def cwd(self, a: Pane) -> Maybe[Path]:
        return a.cwd

    def pin(self, a: Pane) -> bool:
        return a.pin

    def set_open(self, a: Pane, state: Boolean) -> Pane:
        return a.set.open(state)


class MyoUiLayout(UiLayout, tpe=Layout):
    pass


class MyoPaneUiView(UiView, tpe=Pane):

    def state(self, a: Pane) -> ViewState:
        return a.state

    def geometry(self, a: Pane) -> ViewGeometry:
        return a.geometry

    def ident(self, a: Pane) -> Ident:
        return a.ident


class MyoLayoutUiView(UiView, tpe=Layout):

    def state(self, a: Layout) -> ViewState:
        return a.state

    def geometry(self, a: Layout) -> ViewGeometry:
        return a.geometry

    def ident(self, a: Layout) -> Ident:
        return a.ident


def has_ident(ident_spec: IdentSpec) -> Callable[[View], bool]:
    ident = ensure_ident_or_generate(ident_spec)
    def has_ident(view: View) -> bool:
        return view.ident == ident
    return has_ident


__all__ = ('View', 'Layout', 'Pane', 'ViewGeometry', 'has_ident',)
