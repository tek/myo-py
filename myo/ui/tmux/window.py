from typing import Callable

from lenses import lens

from amino import List, __, _, Maybe
from amino.lazy import lazy

from ribosome.record import Record, field, maybe_field

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter, Pane
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

    def pane_lens(self, f: Callable[[Pane], Maybe]):
        return self.root.pane_lens(f) / lens().root.add_lens


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

    @property
    def active_pane(self):
        return self.panes.find(_.active)

__all__ = ('WindowAdapter', 'Window')
