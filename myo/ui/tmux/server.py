import libtmux

from myo.logging import Logging
from myo.ui.tmux.session import SessionAdapter

from tryp import _, List, __


class Server(Logging):

    def __init__(self, native: libtmux.Server) -> None:
        self.native = native

    @property
    def sessions(self):
        return List.wrap(self.native.sessions) / SessionAdapter

    def find_pane_by_id(self, id: int):
        return self.sessions.find_map(__.find_pane_by_id(id))

    @property
    def windows(self):
        return self.sessions // _.windows

    def window(self, id):
        return self.windows.find(__.id_i.contains(id))

    @property
    def panes(self):
        return self.windows // _.panes

    def pane(self, id):
        return self.panes.find(__.id_i.contains(id))

    @property
    def pane_ids(self):
        return self.panes // _.id_i.to_list

    def kill(self):
        return self.native.kill_server()

__all__ = ('Server',)
