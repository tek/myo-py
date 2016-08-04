from tryp import List, __
from tryp.lazy import lazy

from trypnv.record import Record, field

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import parse_window_id


class Window(Record):
    id = field(int)
    root = field(Layout)


class VimWindow(Window):
    pass


class WindowAdapter(Adapter):

    @lazy
    def panes(self):
        return List.wrap(self.native.panes) / PaneAdapter

    def find_pane_by_id(self, id: int):
        return self.panes.find(__.id_i.contains(id))

    @lazy
    def id(self):
        return self.native._window_id

    @lazy
    def id_i(self):
        return parse_window_id(self.id)

    @lazy
    def size(self):
        return int(self.native.width), int(self.native.height)

__all__ = ('WindowAdapter', 'Window')
