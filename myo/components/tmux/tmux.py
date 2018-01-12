import abc

import libtmux
import libtmux.formats

from amino import List, Lists, Map, Boolean, do, Either, Do, Right, _, __, Try
from amino.lazy import lazy
from amino.boolean import false, true

from myo.tmux.data.session import Session
from myo.tmux.data.window import Window
from myo.tmux.data.pane import Pane

from myo.tmux.session import NativeSession
from myo.tmux.pane import PaneData, NativePane
from myo.tmux.window import NativeWindow

libtmux.formats.PANE_FORMATS += [
    'pane_left',
    'pane_top',
]


class NativeServer(libtmux.Server):

    def list_sessions(self):
        return [NativeSession(server=self, **s) for s in self._sessions]


class Tmux:

    @staticmethod
    def cons(socket: str=None) -> 'Tmux':
        server = NativeServer(socket)
        return NativeTmux(server)

    @abc.abstractproperty
    def sessions(self) -> List[NativeSession]:
        ...

    @abc.abstractmethod
    def session(self, session_id: str) -> Either[str, NativeSession]:
        ...

    @abc.abstractproperty
    def pane_data(self) -> List[PaneData]:
        ...

    def kill_server(self) -> None:
        self.server.kill_server()

    @abc.abstractmethod
    def windows(self, session_id: str) -> Either[str, List[NativeWindow]]:
        ...

    @abc.abstractmethod
    def window(self, session_id: str, window_id: str) -> Either[str, NativeWindow]:
        ...

    @abc.abstractmethod
    def window_exists(self, session_id: str, window_id: str) -> Boolean:
        ...

    @abc.abstractmethod
    def create_window(self, session: Session, window: Window) -> Either[str, NativeWindow]:
        ...


class NativeTmux(Tmux):

    def __init__(self, server: libtmux.Server) -> None:
        self.server = server

    @property
    def sessions(self) -> List[NativeSession]:
        return Lists.wrap(self.server.list_sessions())

    def session(self, session_id: str) -> Either[str, NativeSession]:
        return self.sessions.find(_.id == session_id).to_either(f'no such session: {session_id}')

    @lazy
    def pane_data(self):
        return List.wrap(self.server._list_panes()) / Map / PaneData

    def windows(self, session_id: str) -> Either[str, List[NativeWindow]]:
        return self.session(session_id) / __.list_windows()

    def window(self, session_id: str, window_id: str) -> Either[str, NativeWindow]:
        return self.session(session_id) // __.window(window_id)

    def window_exists(self, session_id: str, window_id: str) -> Boolean:
        return self.window(session_id, window_id).replace(true) | false

    @do(Either[str, NativeWindow])
    def create_window(self, session: Session, window: Window) -> Do:
        session_id = yield session.id.to_either('session has no id')
        nsession = yield self.session(session_id)
        yield Try(nsession.create_window, window.name)

    @do(Either[str, NativePane])
    def pane(self, session: Session, window: Window, pane: Pane) -> Do:
        session_id = yield session.id.to_either('session has no id')
        window_id = yield window.id.to_either('window has no id')
        pane_id = yield pane.id.to_either('pane has no id')
        win = yield self.window(session_id, window_id)
        yield win.pane(pane_id)

    @do(Either[str, Either[str, NativePane]])
    def create_pane(self, session: Session, window: Window, pane: Pane) -> Do:
        session_id = yield session.id.to_either('session has no id')
        window_id = yield window.id.to_either('window has no id')
        w = yield self.window(session_id, window_id)
        yield Try(w.create_pane)


class PureTmux(Tmux):

    def __init__(self, _sessions: List[Session], _windows: List[Window], _panes: List[Pane]) -> None:
        self._sessions = _sessions
        self._windows = _windows
        self._panes = _panes

    @property
    def sessions(self) -> List[Session]:
        return self._sessions

__all__ = ('Tmux',)
