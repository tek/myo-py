from typing import Callable

from myo.logging import Logging
from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout

from amino import Maybe, __, _


class TmuxFacade(Logging):

    def __init__(self, state: TmuxState) -> None:
        self.state = state

    def add_to_layout(self, parent: Maybe[str], target: Callable, view: View):
        name = parent | 'root'
        return (
            self.state.layout_lens_ident(name) /
            target /
            __.modify(__.cat(view))
        )

    def add_pane_to_layout(self, parent: Maybe[str], pane: Pane):
        return self.add_to_layout(parent, _.panes, pane)

    def add_layout_to_layout(self, parent: Maybe[str], layout: Layout):
        return self.add_to_layout(parent, _.layouts, layout)

__all__ = ('TmuxFacade',)
