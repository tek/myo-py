import libtmux

from trypnv.record import field, Record

from tryp import List, __

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.window import WindowAdapter


class Session(Record):
    id = field(str)


class SessionHandler:

    def __init__(self, server: libtmux.Server) -> None:
        self.server = server

    def create_pane(self, pane):
        pass


class SessionAdapter(Adapter):

    @property
    def windows(self):
        return List.wrap(self.native.windows) / WindowAdapter

    def find_pane_by_id(self, id: int):
        return self.windows.find_map(__.find_pane_by_id(id))

__all__ = ('Session',)
