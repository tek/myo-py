from typing import Callable

import libtmux

from lenses import lens, Lens

from tryp import List, _, __, curried, Just, Maybe, Map
from tryp.lazy import lazy
from tryp.lens.tree import path_lens_unbound, path_lens_pred
from tryp.task import Task
from tryp.anon import L

from trypnv.machine import may_handle, handle, IO, DataTask, RunTask
from trypnv.record import field, list_field, Record

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.messages import (TmuxOpenPane, TmuxRunCommand,
                                       TmuxCreatePane, TmuxCreateLayout,
                                       TmuxCreateSession, TmuxSpawnSession,
                                       TmuxFindVim, TmuxTest, TmuxLoadDefaults)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import (LayoutDirections, Layout, VimLayout,
                                LinearLayout)
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server
from myo.util import parse_int, view_params
from myo.ui.tmux.window import VimWindow
from myo.ui.tmux.facade import LayoutFacade, PanePath
from myo.ui.tmux.view import View
from myo.plugins.core.message import AddDispatcher
from myo.plugins.tmux.dispatch import TmuxDispatcher

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
        id = self.vim.pvar('tmux_force_vim_pane_id') | self._find_vim_pane_id
        wid = self.vim.pvar('tmux_force_vim_win_id') | self._find_vim_win_id
        vim_w = self.vim.pvar('tmux_vim_width') | 80
        pane = VimPane(id=parse_int(id).to_maybe, name='vim')
        vim_layout = VimLayout(name='vim',
                               direction=LayoutDirections.vertical,
                               panes=List(pane), fixed_size=Just(vim_w),
                               weight=Just(0.8))
        root = LinearLayout(name='root',
                            direction=LayoutDirections.horizontal,
                            layouts=List(vim_layout))
        win = VimWindow(id=wid, root=root)
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
        layout = LinearLayout(name=self.msg.name, direction=direction,
                              **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.layouts, layout)

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        pane = Pane(name=self.msg.name, **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.panes, pane)

    @may_handle(TmuxOpenPane)
    def open(self):
        callbacks = List(
            self.layouts.open_pane,
            self.layouts.pack_path,
        )
        return self._pane_path_mod(_.name == self.msg.name, callbacks)

    @handle(TmuxRunCommand)
    def dispatch(self):
        opt = self.msg.options
        pane_name = opt.get('pane') | self._default_pane_name
        pane = self._pane(pane_name)
        return pane / L(self._run_command)(self.msg.command, _, opt) / RunTask

    @may_handle(TmuxTest)
    def test(self):
        self.log.info('--------- test')
        self.log.info(self.state)

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
    def _find_vim_pane_id(self):
        return -1

    @property
    def _find_vim_win_id(self):
        return -1

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

    @lazy
    def layouts(self):
        return LayoutFacade(self.server)

    @property
    def panes(self):
        return self.layouts.panes

    def new_state(self):
        return TmuxState(server=self.server)

__all__ = ('Plugin', 'Transitions')
