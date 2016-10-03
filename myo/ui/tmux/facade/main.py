from typing import Callable

from myo.logging import Logging
from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import Ident
from myo.ui.tmux.server import Server
from myo.ui.tmux.view_path import PaneLoc
from myo.ui.tmux.facade.view import PaneFacade

from amino import Maybe, __, _, Just, F
from amino.lazy import lazy


class TmuxFacade(Logging):

    def __init__(self, state: TmuxState, server: Server) -> None:
        self.state = state
        self.server = server

    @lazy
    def panes(self):
        return PaneFacade(self.server)

    @lazy
    def sessions(self):
        return self.server.sessions

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

    def pane_loc(self, ident: Ident):
        win = lambda w: Just(w) & w.root.find_pane(ident)
        sess = lambda s: s.windows.find_map(win).map2(lambda a, b: (s, a, b))
        return self.state.sessions.find_map(sess).map3(PaneLoc.create)

    def _focus(self, ident: Ident, f: Callable):
        def run(a):
            return (
                self.find_loc(a)
                .task('pane not found for focus: {}'.format(a)) /
                __.focus()
            )
        return self.pane_loc(ident) // f / run

    def focus(self, ident: Ident):
        return self._focus(ident, Just)

    def fix_focus(self, ident: Ident, alt: Ident):
        def check(a):
            return a.pane.focus.c(Just(a), F(self.pane_loc, alt))
        return self._focus(ident, check)

    def find_loc(self, loc: PaneLoc):
        pane = lambda w: loc.pane.id // w.pane_by_id
        win = lambda s: loc.window.id // s.window_by_id
        return loc.session.id // self.find_session // win // pane

    def find_session(self, id: int):
        return self.sessions.find(__.id_i.contains(id))

__all__ = ('TmuxFacade',)
