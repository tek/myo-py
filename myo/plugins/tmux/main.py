from trypnv.machine import may_handle, handle
from trypnv.record import Record, field, maybe_field, list_field

import tmuxp

from lenses import lens

from tryp import List, F, _, Just, __

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.messages import (TmuxOpenPane, TmuxRun, TmuxCreatePane,
                                       TmuxCreateLayout, TmuxCreateSession,
                                       TmuxSpawnSession, TmuxFindVim)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout, LinearLayout, LayoutDirection
from myo.tmux.session import Session


class TmuxState(Record):
    server = field(tmuxp.Server)
    vim_layout = maybe_field(Layout)
    vim_pane = maybe_field(Pane)
    sessions = list_field()
    layouts = list_field()
    panes = list_field()

    def session(self, id: str):
        return self.sessions.find(_.id == id)


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        @property
        def state(self):
            return self.data.sub_state(self.name, TmuxState)

        def _with_sub(self, state):
            return self.data.with_sub_state(self.name, state)

        @property
        def server(self):
            return self.state.server

        @may_handle(StageI)
        def stage_1(self):
            socket = self.vim.pvar('tmux_socket') | None
            server = tmuxp.Server(socket_name=socket)
            return self._with_sub(TmuxState(server=server)), TmuxFindVim()

        @may_handle(TmuxFindVim)
        def find_vim(self):
            id = self.vim.pvar('tmux_force_vim_pane_id') | self._find_vim_id
            pane = Pane(id=Just(str(id)), name='vim')
            layout = LinearLayout(name='vim',
                                  direction=LayoutDirection.horizontal,
                                  panes=List(pane))
            new_state = (
                self.state.setter.vim_layout(Just(layout))
                .setter.vim_pane(Just(pane))
                .append1.layouts(layout)
                .append1.panes(pane)
            )
            return self._with_sub(new_state)

        @property
        def _find_vim_id(self):
            return '-1'

        @handle(TmuxCreateSession)
        def create_session(self):
            return (
                self.msg.options.get('name') /
                (lambda n: Session(id=n)) /
                List /
                self.state.append.sessions /
                self._with_sub
            )

        @may_handle(TmuxSpawnSession)
        def spawn_session(self):
            s = self.state.session(self.msg.id)
            self.server.new_session(session_name=s.x)

        @may_handle(TmuxCreateLayout)
        def create_layout(self):
            layout = Layout(self.server)
            f = F(self.state.append.layouts) >> self._with_sub
            return f(layout)

        @handle(TmuxCreatePane)
        def create_pane(self):
            layout_lens = (
                self.msg.options.get('layout') //
                self._layout_lens /
                _.panes
            )
            pn = self.msg.options.get('name') / (lambda n: List(Pane(name=n)))
            return layout_lens.product(pn).map2(_ + _) / self._with_sub

        @may_handle(TmuxOpenPane)
        def open(self):
            pane = self._find_pane(self.msg.name)
            self.log.verbose(self.state.layouts)
            self.log.verbose(pane)

        @may_handle(TmuxRun)
        def dispatch(self):
            pass

        def _layout_lens(self, name):
            return (self.state.layouts.index_where(_.name == name) /
                    lens(self.state).layouts.__getitem__)

        def _find_pane(self, name):
            return self.state.layouts.deep_find(__.find_pane(name)).flatten

__all__ = ('Plugin',)
