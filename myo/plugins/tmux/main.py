from typing import Callable

import libtmux

from lenses import lens, Lens

from tryp import List, F, _, Just, __, Maybe, curried
from tryp.lazy import lazy
from tryp.lens.tree import path_lens, path_lens_unbound
from tryp.task import Task
from tryp.anon import L

from trypnv.machine import may_handle, handle, IO, DataTask
from trypnv.record import field, list_field

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.messages import (TmuxOpenPane, TmuxRun, TmuxCreatePane,
                                       TmuxCreateLayout, TmuxCreateSession,
                                       TmuxSpawnSession, TmuxFindVim, TmuxTest)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import (LayoutDirection, Layout, LayoutHandler,
                                PanePath, VimLayout)
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server
from myo.util import parse_int


class TmuxState(Layout):
    server = field(Server)
    sessions = list_field()

    def session(self, id: str):
        return self.sessions.find(_.id == id)

    @property
    def vim_layout(self):
        return self.layouts.find(lambda a: isinstance(a, VimLayout))

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
        id = self.vim.pvar('tmux_force_vim_pane_id') | self._find_vim_id
        pane = VimPane(id=parse_int(id).to_maybe, name='vim', open=True)
        layout = VimLayout(name='vim',
                           direction=LayoutDirection.horizontal,
                           panes=List(pane))
        new_state = self.state.append1.layouts(layout)
        return self.with_sub(new_state)

    @property
    def _find_vim_id(self):
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
        layout_lens = (
            self.msg.options.get('layout') //
            self._layout_lens /
            _.panes
        )
        pn = self.msg.options.get('name') / (lambda n: List(Pane(name=n)))
        return layout_lens.product(pn).map2(_ + _) / self.with_sub

    @may_handle(TmuxOpenPane)
    def open(self):
        return self._pane_path_mod(_.name == self.msg.name,
                                   List(self.layout_handler.open_pane))

    Callback = Callable[[PanePath], Task]

    def _pane_path_mod(self, pred, callbacks: List[Callback]):
        ''' find the pane satisfying **pred** and successively call
        the functions in **callbacks** with a PanePath argument
        '''
        def dispatch(state, l, f):
            bound = l.bind(state)
            path = PanePath.try_create(List.wrap(bound.get()))
            return Task.from_either(path) // f / _.to_list / bound.set
        def iterate(state, l: Lens) -> Task:
            return callbacks.fold_left(Task.now(state))(
                lambda a, b: a // L(dispatch)(_, l, b))
        def go(state):
            l = self._pane_path(pred)(state)
            return (
                Task.from_maybe(l, 'lens path failed') //
                L(iterate)(state, _)
            )
        return DataTask(
            _ /
            self._state //
            go /
            self.with_sub
        )

    @curried
    def _pane_path(self, pred, state):
        f = __.panes.find_lens_pred(pred).map(lens().panes.add_lens)
        sub = _.layouts
        return path_lens_unbound(state, sub, f)

    def _open_pane(self, pane):
        return pane.set(open=True)

    @may_handle(TmuxRun)
    def dispatch(self):
        pass

    def _layout_lens(self, name):
        return (self.state.layouts.index_where(_.name == name) /
                (lambda i: lens(self.state).layouts[i]))

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
        return TmuxState(name='state', server=self.server)

__all__ = ('Plugin', 'Transitions')
