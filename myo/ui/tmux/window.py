from amino import List, __
from amino.lazy import lazy

from ribosome.record import Record, field, maybe_field

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import parse_window_id


class Window(Record):
    id = maybe_field(int)
    root = field(Layout)

    @property
    def desc(self):
        id = self.id / ' @{}'.format | ''
        return 'W{}'.format(id)

    @property
    def name(self):
        return self.root.name


class VimWindow(Window):

    @property
    def desc(self):
        return 'V{}'.format(super().desc)


class WindowAdapter(Adapter):

    @lazy
    def panes(self):
        return List.wrap(self.native.panes) / PaneAdapter

    def pane_by_id(self, id: int):
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
