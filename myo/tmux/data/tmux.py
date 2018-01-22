from amino import Dat, List, Nil, Either, _, Just
from amino.lenses.lens import lens

from myo.tmux.data.session import Session
from myo.tmux.data.window import Window
from myo.tmux.data.layout import Layout
from myo.tmux.data.pane import Pane
from myo.ui.data.space import Space
from myo.ui.data.window import Window as UiWindow
from myo.ui.data.view import Pane as UiPane


class TmuxData(Dat['TmuxData']):

    @staticmethod
    def cons(
            sessions: List[Session]=Nil,
            windows: List[Window]=Nil,
            layouts: List[Layout]=Nil,
            panes: List[Pane]=Nil,
    ) -> 'TmuxData':
        return TmuxData(
            sessions,
            windows,
            layouts,
            panes,
        )

    def __init__(
            self,
            sessions: List[Session],
            windows: List[Window],
            layouts: List[Layout],
            panes: List[Pane],
    ) -> None:
        self.sessions = sessions
        self.windows = windows
        self.layouts = layouts
        self.panes = panes

    def add_pane(self, pane: Pane) -> 'TmuxData':
        return self.append1.panes(pane)

    def pane_by_name(self, name: str) -> Either[str, Pane]:
        return self.panes.find(_.name == name).to_either(f'no pane named `{name}`')

    def update_pane(self, pane: Pane) -> 'TmuxData':
        return lens.panes.Each().Filter(_.name == pane.name).set(pane)(self)

    def set_pane_id(self, pane: Pane, id: str) -> 'TmuxData':
        return self.update_pane(pane.copy(id=Just(id)))

    def session_for_space(self, space: Space) -> Either[str, Session]:
        return self.sessions.find(_.space == space.ident).to_either(f'no session for {space}')

    def window_for_window(self, window: UiWindow) -> Either[str, Window]:
        return self.windows.find(_.window == window.ident).to_either(f'no window for {window}')

    def pane_for_pane(self, pane: UiPane) -> Either[str, Pane]:
        return self.panes.find(_.pane == pane.ident).to_either(lambda: f'no pane for {pane}')


__all__ = ('TmuxData',)
