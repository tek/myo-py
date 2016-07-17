from tryp import List, __

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter


class WindowAdapter(Adapter):

    @property
    def panes(self):
        return List.wrap(self.native.panes) / PaneAdapter

    def find_pane_by_id(self, id: int):
        return self.panes.find(__.id_i.contains(id))

__all__ = ('WindowAdapter',)
