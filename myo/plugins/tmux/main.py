from typing import Callable

import libtmux

import psutil

from lenses import lens

from tryp import List, _, __, Just, Maybe, Map, Right, Try
from tryp.lazy import lazy
from tryp.task import Task
from tryp.anon import L

from trypnv.machine import may_handle, handle, DataTask, either_msg
from trypnv.record import field, list_field, Record

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.messages import (TmuxOpenPane, TmuxRunCommand,
                                       TmuxCreatePane, TmuxCreateLayout,
                                       TmuxCreateSession, TmuxSpawnSession,
                                       TmuxFindVim, TmuxInfo, TmuxLoadDefaults,
                                       TmuxClosePane)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import LayoutDirections, Layout, VimLayout
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server
from myo.util import parse_int, view_params
from myo.ui.tmux.window import VimWindow
from myo.ui.tmux.facade import LayoutFacade
from myo.ui.tmux.view import View
from myo.plugins.core.message import AddDispatcher
from myo.plugins.tmux.dispatch import TmuxDispatcher
from myo.ui.tmux.util import format_state
from myo.ui.tmux.pane_path import PanePathMod

_is_vim_window = lambda a: isinstance(a, VimWindow)
_is_vim_layout = lambda a: isinstance(a, VimLayout)


def _name_ppm(name):
    return PanePathMod(pred=_.name == name)


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

    @property
    def server(self):
        return self.state.server

    @property
    def layouts(self):
        return self.machine.layouts

    @property
    def panes(self):
        return self.machine.panes

    @may_handle(StageI)
    def stage_1(self):
        ''' Initialize the state. If it doesn't exist, Env will create
        it using the constructor function supplied in *Plugin.state*
        '''
        default = self.pflags.tmux_use_defaults.maybe(TmuxLoadDefaults())
        msgs = List(AddDispatcher(), self.with_sub(self.state), TmuxFindVim())
        return msgs + default.to_list

    @may_handle(AddDispatcher)
    def add_dispatcher(self):
        return self.data + TmuxDispatcher()

    @may_handle(TmuxFindVim)
    def find_vim(self):
        vim_pid = self._vim_pid
        pane = vim_pid // self._find_vim_pane
        id = (
            (self.vim.pvar('tmux_force_vim_pane_id') // parse_int)
            .or_else(pane // _.id_i)
        )
        wid = (
            self.vim.pvar('tmux_force_vim_win_id')
            .or_else(pane // _.window_id_i)
        )
        vim_w = self.vim.pvar('tmux_vim_width').or_else(Just(85))
        pane = VimPane(id=id.to_maybe, name='vim', pid=vim_pid.to_maybe)
        vim_layout = VimLayout(name='vim',
                               direction=LayoutDirections.vertical,
                               panes=List(pane), fixed_size=vim_w)
        root = Layout(name='root',
                      direction=LayoutDirections.horizontal,
                      layouts=List(vim_layout))
        win = VimWindow(id=wid.to_maybe, root=root)
        new_state = self.state.append1.windows(win)
        return self.with_sub(new_state)

    @may_handle(TmuxLoadDefaults)
    def load_defaults(self):
        main = TmuxCreateLayout('main', options=Map(parent='root'))
        make = TmuxCreatePane('make', options=Map(parent='main'))
        return main, make

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

    @handle(TmuxCreateLayout)
    def create_layout(self):
        opts = self.msg.options
        dir_s = opts.get('direction') | 'vertical'
        direction = LayoutDirections.parse(dir_s)
        layout = Layout(name=self.msg.name, direction=direction,
                        **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.layouts, layout)

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        pane = Pane(name=self.msg.name, **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.panes, pane)

    @may_handle(TmuxOpenPane)
    def open(self):
        return self._open_pane_ppm(self.msg.name)

    @may_handle(TmuxClosePane)
    def close(self):
        return self._close_pane_ppm(self.msg.name)

    @may_handle(TmuxRunCommand)
    def dispatch(self):
        opt = self.msg.options
        pane_name = opt.get('pane') | self._default_pane_name
        def go(path):
            return (self._run_command(self.msg.command, path.pane, opt) /
                    (lambda a: Right(path)))
        ppm = self._open_pane_ppm(pane_name) + go
        return self._run_ppm(ppm)

    @may_handle(PanePathMod)
    def pane_path_mod(self):
        return self._run_ppm(self.msg)

    @may_handle(TmuxInfo)
    def info(self):
        self.log.info('\n'.join(format_state(self.state)))

    def _wrap_window(self, data, callback):
        state = self._state(data)
        win = Task.from_maybe(state.vim_window, 'no vim window')
        update = __.map(L(self._with_vim_window)(data, state, _))
        return win // callback / update

    def _run_ppm(self, ppm):
        return DataTask(_ // L(self._wrap_window)(_, ppm.run) / either_msg)

    def _open_pane_ppm(self, name: str):
        # cannot reference self.layouts.pack_path directly, because panes
        # are cached
        return _name_ppm(name) / self._open_pane / self._pack_path

    def _close_pane_ppm(self, name: str):
        # cannot reference self.layouts.pack_path directly, because panes
        # are cached
        return _name_ppm(name) / self._close_pane / self._pack_path

    def _open_pane(self, w):
        return self.layouts.open_pane(w)

    def _close_pane(self, w):
        return self.layouts.close_pane(w)

    def _pack_path(self, w):
        return self.layouts.pack_path(w)

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

    def _add_to_layout(self, parent: Maybe[str], target: Callable, view: View):
        name = parent | 'root'
        return (
            self._layout_lens_bound(name) /
            target /
            __.modify(__.cat(view)) /
            self.with_sub
        )

    def _pane_lens(self, f: Callable):
        return Layout.pane_lens(self.state, f)

    def _pane(self, name):
        return self.state.vim_window // __.root.find_pane_deep(name)

    def _default_pane_name(self):
        return 'make'

    @property
    def _vim_pid(self):
        return (
            self.vim.call('getpid').to_either('no pid') /
            psutil.Process //
            (lambda p: Try(p.ppid))
        )

    def _find_vim_pane(self, vim_pid):
        return self.server.panes.find(__.pid.contains(vim_pid))

    def _run_command(self, command, pane, options):
        return self.panes.run_command(pane, command)


class Plugin(MyoComponent):

    Transitions = Transitions

    @lazy
    def native_server(self):
        socket = self.vim.pvar('tmux_socket') | None
        return libtmux.Server(socket_name=socket)

    @lazy
    def server(self):
        return Server(self.native_server)

    @property
    def layouts(self):
        return LayoutFacade(self.server)

    @property
    def panes(self):
        return self.layouts.panes

    def new_state(self):
        return TmuxState(server=self.server)

__all__ = ('Plugin', 'Transitions')
