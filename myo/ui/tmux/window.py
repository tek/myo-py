import re
from tryp import List, __

from trypnv.record import Record, field

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter
from myo.ui.tmux.layout import Layout
from myo.util import parse_id

_id_re = re.compile('^@(\d+)$')


def parse_window_id(value):
    return parse_id(value, _id_re, 'window')


class Window(Record):
    id = field(int)
    root = field(Layout)


class VimWindow(Window):
    pass


class WindowAdapter(Adapter):

    @property
    def panes(self):
        return List.wrap(self.native.panes) / PaneAdapter

    def find_pane_by_id(self, id: int):
        return self.panes.find(__.id_i.contains(id))

    @property
    def id(self):
        return self.native._window_id

    @property
    def id_i(self):
        return parse_window_id(self.id)

__all__ = ('WindowAdapter', 'Window')
