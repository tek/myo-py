from typing import Callable, Tuple

from amino import Maybe, __, _, Just, Task, Either, F, L, Right, List, Map

from myo.logging import Logging
from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import Ident
from myo.ui.tmux.server import Server, NativeServer
from myo.ui.tmux.view_path import (ViewLoc, ViewPath, PanePathMod,
                                   LayoutPathMod, ViewPathMod)
from myo.ui.tmux.session import Session
from myo.ui.tmux.window import Window
from myo.ui.tmux.facade.window import WindowFacade


class TmuxFacade(Logging):

    def __init__(self, state: TmuxState, socket=None, options: Map=Map()
                 ) -> None:
        self.state = state
        self.socket = socket
        self.options = options

    @property
    def native_server(self):
        return NativeServer(socket_name=self.socket)

    @property
    def _fresh_server(self):
        return Server(self.native_server)

    @property
    def server(self):
        return self._fresh_server

    @property
    def sessions(self):
        return self.server.sessions

    def native_session(self, id: int):
        return self.sessions.find(__.id_i.contains(id))

    def native_window(self, session, window):
        win = lambda s: window.id // s.window_by_id
        return ((session.id // self.native_session // win)
                .to_either('no native window for {}'.format(window)))

    def _view_loc(self, ident: Ident, attr: Callable, desc: str, tpe: type
                  ) -> Either[str, ViewLoc]:
        win = lambda w: Just(w) & attr(w.root)(ident)
        sess = lambda s: s.windows.find_map(win).map2(lambda a, b: (s, a, b))
        return (
            self.state.sessions
            .find_map(sess)
            .to_either('{} not found: {}'.format(desc, ident))
            .map3(ViewLoc.create)
        )

    def pane_loc(self, ident: Ident) -> Either[str, ViewLoc]:
        return self._view_loc(ident, _.find_pane, 'pane', ViewLoc)

    def view_loc(self, ident: Ident) -> Either[str, ViewLoc]:
        return self._view_loc(ident, _.find_view, 'view', ViewLoc)

    def window(self, session: Session, window: Window):
        return (self.native_window(session, window) /
                L(WindowFacade)(session, window, _))

    def window_task(self, session, window) -> Task[WindowFacade]:
        return Task.call(self.window, session, window).join_either

    def loc_window(self, loc: ViewLoc) -> WindowFacade:
        return self.window(loc.session, loc.window)

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

    def pane_window(self, ident: Ident
                    ) -> Either[str, Tuple[WindowFacade, ViewLoc]]:
        f = lambda loc: self.loc_window(loc) & Right(loc.view)
        return self.pane_loc(ident) // f

    def pane_window_task(self, ident: Ident
                         ) -> Task[Tuple[WindowFacade, ViewLoc]]:
        return Task.call(self.pane_window, ident).join_either

    def view_window(self, ident: Ident
                    ) -> Either[str, Tuple[WindowFacade, ViewLoc]]:
        f = lambda loc: self.loc_window(loc) & Right(loc.view)
        return self.view_loc(ident) // f

    def path_window(self, path: ViewPath) -> Maybe[WindowFacade]:
        return self.window(path.session, path.window)

    def path_window_task(self, path: ViewPath) -> Task[WindowFacade]:
        return self.window_task(path.session, path.window)

    def focus(self, ident: Ident):
        return self._focus(ident, Just)

    def fix_focus(self, ident: Ident, alt: Ident):
        check = lambda a: a.view.focus.c(Just(a), F(self.pane_loc, alt))
        return self._focus(ident, check)

    def _focus(self, ident: Ident, f: Callable):
        run = lambda l: self.loc_window(l) / __.focus(l.view)
        return self.pane_loc(ident) // f // run

    @property
    def pack_sessions(self):
        return (self.state.sessions / self.pack_windows).sequence(Task)

    def pack_windows(self, session: Session):
        return session.windows.traverse(L(self.pack_window)(session, _), Task)

    def pack_window(self, session: Session, window: Window
                    ) -> Task[Either[str, Window]]:
        return self.window_task(session, window) // _.pack

    def open_pane(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        return self.path_window_task(path) // __.open_pane(path)

    def kill_process(self, ident: Ident, signals):
        run = lambda win, pane: win.kill_process(pane, signals)
        return self.pane_window_task(ident).flat_map2(run)

    @property
    def close_all(self):
        return (
            self.state.possibly_open_panes //
            _.id
        ).traverse(self.close_id, Task)

    def close_id(self, id: int):
        return self.server.cmd('kill-pane', '-t', '%{}'.format(id))

    def view_open(self, ident: Ident):
        return self.view_window(ident).map2(lambda w, v: w.view_open(v))

    def _run_vpm(self, vpm):
        return self._state_task(vpm.run, self.options)

    def _ident_pm(self, tpe: type, ident: Ident):
        return tpe(pred=__.has_ident(ident), options=self.options)

    def _ident_ppm(self, ident: Ident):
        return self._ident_pm(PanePathMod, ident)

    def _ident_lpm(self, ident: Ident):
        return self._ident_pm(LayoutPathMod, ident)

    def _ident_vpm(self, ident: Ident):
        return self._ident_pm(ViewPathMod, ident)

    def open_pane_ppm(self, name: Ident):
        return self._ident_vpm(name) / self.open_pane

    def close_pane_ppm(self, ident: Ident):
        def run(w, v):
            return self._ident_ppm(ident) / w.close_pane_path
        return self.pane_window(ident).map2(run)

    def run_command_ppm(self, pane_ident: Ident, line: str, in_shell: bool,
                        kill: bool, signals: List[str]):
        win = lambda path: self.path_window_task(path)
        def check_running(path):
            pane_kill = path.view.kill
            return Task.now(Right(path)) if in_shell else (
                win(path) //
                __.ensure_not_running(
                    path.view, kill=kill or pane_kill, signals=signals) /
                __.replace(path)
            )
        def pipe(path):
            return (
                win(path) //
                __.pipe(path.view, self.state.instance_id) /
                path.setter.view /
                Right
            )
        run = lambda path: (win(path) // __.run_command_line(path.view, line))
        def pid(path):
            return (
                win(path) //
                __.command_pid(path.view) /
                (lambda a: path.map_view(__.set(pid=a))) /
                Right
            )
        ppm = (self._ident_vpm
               if self.pane_open(pane_ident) else
               self.open_pane_ppm)
        return (((ppm(pane_ident) + check_running) / pipe) % run) / pid

    def pane_mod(self, ident: Ident, f: Callable[[Pane], Pane]):
        return self._mod(self._ident_ppm, ident, f)

    def view_mod(self, ident: Ident, f: Callable[[View], View]):
        return self._mod(self._ident_vpm, ident, f)

    def _mod(self, ctor: Callable, ident: Ident, f: Callable[[View], View]):
        def g(path):
            return Task.now(Right(path.map_view(f)))
        return ctor(ident) / g

    def pinned_panes(self, ident):
        def layout(l):
            target = l.panes.find(__.has_ident(ident))
            sub = (l.layouts // layout)
            add = (List() if sub.empty and target.empty else
                   l.panes.filter(_.pin))
            return sub + add
        return (self.state.all_windows / _.root // layout) / _.ident

    def pane_open(self, ident: Ident):
        return self.pane_window(ident).map2(__.pane_open(_)).true

    def view_exists(self, ident: Ident):
        return self.view_loc(ident).present

__all__ = ('TmuxFacade',)
