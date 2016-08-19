import libtmux

from ribosome.record import field, Record

from amino import List, __, _
from amino.lazy import lazy

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.window import WindowAdapter
from myo.ui.tmux.util import parse_session_id


class Session(Record):
    id = field(str)


class SessionHandler:

    def __init__(self, server: libtmux.Server) -> None:
        self.server = server

    def create_pane(self, pane):
        pass


class SessionAdapter(Adapter):

    @lazy
    def id(self):
        return self.native.id

    @property
    def id_i(self):
        return parse_session_id(self.id)

    @lazy
    def windows(self):
        return List.wrap(self.native.windows) / WindowAdapter

    def window_by_id(self, id):
        return self.windows.find(__.id_i.contains(id))

    def find_pane_by_id(self, id: int):
        return self.windows.find_map(__.pane_by_id(id))

__all__ = ('Session',)
