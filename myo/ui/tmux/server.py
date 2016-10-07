import libtmux
import libtmux.formats

from myo.logging import Logging
from myo.ui.tmux.session import SessionAdapter, NativeSession
from myo.ui.tmux.pane import PaneData
from amino import _, List, __, Map
from amino.task import task
from amino.lazy import lazy

libtmux.formats.PANE_FORMATS += [
    'pane_left',
    'pane_top',
]


class NativeServer(libtmux.Server):

    def list_sessions(self):
        return [NativeSession(server=self, **s) for s in self._sessions]


class Server(Logging):

    def __init__(self, native: NativeServer) -> None:
        self.native = native

    @lazy
    def sessions(self):
        return List.wrap(self.native.sessions) / SessionAdapter

    def session_by_id(self, id: int):
        return self.sessions.find(__.id_i.contains(id))

    @lazy
    def windows(self):
        return self.sessions // _.windows

    def window(self, id):
        return self.windows.find(__.id_i.contains(id))

    @lazy
    def panes(self):
        return self.windows // _.panes

    def pane(self, id):
        return self.panes.find(__.id_i.contains(id))

    @lazy
    def pane_data(self):
        return List.wrap(self.native._list_panes()) / Map / PaneData

    @lazy
    def pane_ids(self):
        return self.pane_data // _.id_i.to_list

    def kill(self):
        return self.native.kill_server()

    @task
    def cmd(self, *a, **kw):
        return self.native.cmd(*a, **kw)

__all__ = ('Server',)
