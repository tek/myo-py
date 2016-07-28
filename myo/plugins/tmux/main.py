from typing import Callable

import libtmux

from lenses import lens, Lens

from tryp import List, F, _, __, curried, Just
from tryp.lazy import lazy
from tryp.lens.tree import path_lens_unbound, path_lens_pred
from tryp.task import Task
from tryp.anon import L

from trypnv.machine import may_handle, handle, IO, DataTask
from trypnv.record import field, list_field, Record

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.messages import (TmuxOpenPane, TmuxRun, TmuxCreatePane,
                                       TmuxCreateLayout, TmuxCreateSession,
                                       TmuxSpawnSession, TmuxFindVim, TmuxTest)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import LayoutDirection, Layout, VimLayout
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server
from myo.util import parse_int, optional_params
from myo.ui.tmux.window import VimWindow
from myo.ui.tmux.layout_handler import LayoutHandler, PanePath

_is_vim_window = lambda a: isinstance(a, VimWindow)
_is_vim_layout = lambda a: isinstance(a, VimLayout)


class TmuxState(Record):
    server = field(Server)
    sessions = list_field()
    windows = list_field()

    @property
    def vim_window(self):
        return self.windows.find(_is_vim_window)

    @property
    def vim_window_lens(self):
        return (self.windows.find_lens_pred(_is_vim_window) /
                lens(self).windows.add_lens)

    @property
    def vim_layout(self):
        return self.vim_window // __.layouts.find(_is_vim_layout)

    @property
    def vim_layout_lens(self):
        return (
            self.vim_layout //
            __.layouts.find_lens_pred(_is_vim_layout) /
            lens(self).windows.add_lens
        )

    @property
    def vim_pane(self):
        return self.vim_layout / _.panes / _.head


class Transitions(MyoTransitions):

    def _state(self, data):
        return data.sub_state(self.name, self.machine.new_state)

    @property
    def state(self):
        return self._state(self.data)

    def _with_sub(self, data, state):
        return data.with_sub_state(self.name, state)

    def with_sub(self, state):
        return self._with_sub(self.data, state)

    def _with_root(self, data, state, root):
        l = state.vim_window_lens / _.root
        new_state = l / __.set(root) | state
        return self._with_sub(data, new_state)

    def _with_vim_window(self, data, state, win):
        new_state = state.vim_window_lens / __.set(win) | state
        return self._with_sub(data, new_state)

    def with_sub_and_msgs(self, state, msgs):
        return (self.with_sub(state),) + msgs

    def with_sub_from_io(self, io):
        return IO(perform=io / self.with_sub)

    @property
    def server(self):
        return self.state.server

    @property
    def layout_handler(self):
        return self.machine.layout_handler

    @may_handle(StageI)
    def stage_1(self):
        ''' Initialize the state. If it doesn't exist, Env will
        create it using the constructor function supplied in
        *Plugin.state*
        '''
        return self.with_sub(self.state), TmuxFindVim()

    @may_handle(TmuxFindVim)
    def find_vim(self):
        id = self.vim.pvar('tmux_force_vim_pane_id') | self._find_vim_pane_id
        wid = self.vim.pvar('tmux_force_vim_win_id') | self._find_vim_win_id
        pane = VimPane(id=parse_int(id).to_maybe, name='vim',
                       fixed_size=Just(60), weight=Just(0.8))
        layout = VimLayout(name='vim',
                           direction=LayoutDirection.horizontal,
                           panes=List(pane))
        win = VimWindow(id=wid, root=layout)
        new_state = self.state.append1.windows(win)
        return self.with_sub(new_state)

    @property
    def _find_vim_pane_id(self):
        return -1

    @property
    def _find_vim_win_id(self):
        return -1

    @handle(TmuxCreateSession)
    def create_session(self):
        return (
            self.msg.options.get('name') /
            (lambda n: Session(id=n)) /
            List /
            self.state.append.sessions /
            self.with_sub
        )

    @may_handle(TmuxSpawnSession)
    def spawn_session(self):
        s = self.state.session(self.msg.id)
        self.server.new_session(session_name=s.x)

    @may_handle(TmuxCreateLayout)
    def create_layout(self):
        layout = Layout(self.server)
        f = F(self.state.append.layouts) >> self.with_sub
        return f(layout)

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        layout_lens = (
            opts.get('layout') //
            self._layout_lens_bound /
            _.panes
        )
        optional = optional_params(opts, 'min_size', 'max_size', 'fixed_size',
                                   'position', 'weight')
        pn = opts.get('name') / (lambda n: List(Pane(name=n, **optional)))
        return layout_lens.product(pn).map2(_ + _) / self.with_sub

    @may_handle(TmuxOpenPane)
    def open(self):
        callbacks = List(
            self.layout_handler.open_pane,
            self.layout_handler.pack_path,
        )
        return self._pane_path_mod(_.name == self.msg.name, callbacks)

    Callback = Callable[[PanePath], Task]

    def _pane_path_mod(self, pred, callbacks: List[Callback]):
        ''' find the pane satisfying **pred** and successively call
        the functions in **callbacks** with a PanePath argument
        '''
        def dispatch(win, unbound_lens, f):
            # FIXME win is passed to f but changes to win are discarded because
            # it is not part of the lens
            bound = unbound_lens.bind(win.root)
            path = PanePath.try_create(win, List.wrap(bound.get()))
            return (Task.from_either(path) // f / _.to_list / bound.set /
                    win.setter.root)
        def iterate(win, l: Lens) -> Task:
            return callbacks.fold_left(Task.now(win))(
                lambda a, b: a // L(dispatch)(_, l, b))
        def go(win):
            l = self._pane_path(pred)(win.root)
            return (
                Task.from_maybe(l, 'lens path failed') //
                L(iterate)(win, _)
            )
        def wrap_window(data):
            state = self._state(data)
            win = Task.from_maybe(state.vim_window, 'no vim window')
            return win // go / L(self._with_vim_window)(data, state, _)
        return DataTask(_ // wrap_window)

    @curried
    def _pane_path(self, pred, root):
        f = __.panes.find_lens_pred(pred).map(lens().panes.add_lens)
        sub = _.layouts
        return path_lens_unbound(root, sub, f)

    @curried
    def _pane_path_bound(self, pred, root):
        return self._pane_path(pred)(root) / __.bind(root)

    @curried
    def _layout_path_bound(self, pred, root):
        return path_lens_pred(root, _.layouts, pred)

    @may_handle(TmuxRun)
    def dispatch(self):
        pass

    def _layout_lens_bound(self, name):
        def sub(a):
            return a.layouts.find_lens(ll) / lens().layouts.add_lens
        def ll(l):
            return Just(lens()) if l.name == name else sub(l)
        return (
            self.state.windows
            .find_lens(lambda a: ll(a.root) / lens().root.add_lens) /
            lens(self.state).windows.add_lens
        )

    def _pane_lens(self, f: Callable):
        return Layout.pane_lens(self.state, f)

    @may_handle(TmuxTest)
    def test(self):
        self.log.verbose('--------- test')
        self.log.verbose(self.state)


class Plugin(MyoComponent):

    Transitions = Transitions

    @lazy
    def native_server(self):
        socket = self.vim.pvar('tmux_socket') | None
        return libtmux.Server(socket_name=socket)

    @lazy
    def server(self):
        return Server(self.native_server)

    @lazy
    def layout_handler(self):
        return LayoutHandler(self.server)

    def new_state(self):
        return TmuxState(server=self.server)

__all__ = ('Plugin', 'Transitions')
