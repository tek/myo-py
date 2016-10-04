import time
import signal
from typing import Callable

from psutil import Process

from ribosome.machine.state import Info

from myo.logging import Logging
from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane, PaneAdapter
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import Ident
from myo.ui.tmux.server import Server
from myo.ui.tmux.view_path import ViewLoc, ViewPath
from myo.ui.tmux.facade.view import PaneFacade, LayoutFacade
from myo.ui.tmux.session import Session
from myo.ui.tmux.window import Window
from myo.ui.tmux.pack import WindowPacker

from amino import (Maybe, __, _, Just, F, Task, Either, I, Right, Left, L,
                   List)
from amino.lazy import lazy
from amino.task import task

from ribosome.machine.transition import Fatal, NothingToDo


class TmuxFacade(Logging):

    def __init__(self, state: TmuxState, server: Server) -> None:
        self.state = state
        self.server = server

    @lazy
    def layouts(self):
        return LayoutFacade(self.server)

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
        return self.state.sessions.find_map(sess).map3(ViewLoc.create)

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
            return a.view.focus.c(Just(a), F(self.pane_loc, alt))
        return self._focus(ident, check)

    def find_loc(self, loc: ViewLoc):
        pane = lambda w: loc.view.id // w.pane_by_id
        win = lambda s: loc.window.id // s.window_by_id
        return loc.session.id // self.find_session // win // pane

    def find_loc_task(self, loc: ViewLoc):
        return (Task.call(self.find_loc, loc)
                .merge_maybe('view not found: {}'.format(loc)))

    def find_session(self, id: int):
        return self.sessions.find(__.id_i.contains(id))

    def find_window(self, session, window):
        win = lambda s: window.id // s.window_by_id
        return session.id // self.find_session // win

    def open_pane(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        v = path.view
        def open(pane):
            def apply(layout):
                set = path.is_pane.cata(I, lambda a: v.replace_pane(a))
                return (
                    self._split_pane(path, layout, pane) /
                    set /
                    path.setter.view /
                    Right
                )
            return (self._pane_opener(path, pane).eff(Either) // apply).value
        view = (Task.now(v) if path.is_pane else
                v.panes.head.task('{} has no panes'.format(v)))
        return view // open

    def _pane_opener(self, path: ViewPath, pane: Pane
                     ) -> Task[Either[str, Layout]]:
        def find_layout():
            return (path.layouts.reversed.find(self.layouts.layout_open)
                    .to_either(
                        Fatal('no open layout when trying to open pane')))
        return Task.now(
            self.panes.is_open(pane).no.flat_either_call(
                Left(NothingToDo('{!r} already open'.format(pane))),
                find_layout,
            )
        )

    def _split_pane(self, path, layout, pane) -> Task[Pane]:
        return self.layouts.ref_pane_fatal(layout) / (
            lambda a:
            self.find_loc(ViewLoc.create(path.session, path.window, a)) /
            __.split(layout.horizontal) /
            PaneAdapter /
            pane.open |
            pane
        )

    @property
    def pack_sessions(self):
        return (self.state.sessions / self.pack_windows).sequence(Task)

    def pack_windows(self, session: Session):
        return session.windows.traverse(L(self.pack_window)(session, _), Task)

    def pack_path(self, path: ViewPath):
        return self.pack_window(path.session, path.window) / __.replace(path)

    def pack_window(self, session: Session, window: Window
                    ) -> Task[Either[str, Window]]:
        return WindowPacker(self, session, window).run

    def run_command_line(self, loc: ViewLoc, line: str):
        return (
            self.find_loc_task(loc) /
            __.run_command(line)
        )

    def ensure_not_running(self, loc: ViewLoc, kill=False,
                           signals=List('kill')):
        def handle(pa):
            return (
                Task.now(Right(True))
                if pa.not_running else
                self._kill_process(pa, signals=signals)
                if loc.view.kill or kill else
                Task.now(Left('command already running'))
            )
        return self.find_loc_task(loc) // handle

    def command_pid(self, loc: ViewLoc):
        return self.find_loc_task(loc) / _.command_pid

    def kill_process(self, ident: Ident, signals):
        return (
            Task.from_maybe(self.pane_loc(ident),
                            'pane not found: {}'.format(ident)) //
            self.find_loc_task //
            L(self._kill_process)(_, signals)
        )

    @task
    def _kill_process(self, adapter, signals):
        def _wait_killed(timeout):
            start = time.time()
            while time.time() - start > timeout and adapter.running:
                time.sleep(.1)
        def kill(signame):
            if adapter.running:
                sig = getattr(signal, 'SIG{}'.format(signame.upper()),
                              signal.SIGINT)
                adapter.command_pid / Process / __.send_signal(sig)
                _wait_killed(3)
            return adapter.not_running
        return (
            signals.find(kill) /
            'process killed by signal {}'.format /
            Info /
            Right |
            Left(Fatal('could not kill running process'))
        )

__all__ = ('TmuxFacade',)
