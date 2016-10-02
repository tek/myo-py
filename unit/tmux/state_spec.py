from unit._support.spec import UnitSpec

from amino import List, Just, __, _
from amino.lazy import lazy

from myo.plugins.tmux.main import TmuxState
from myo.ui.tmux.server import Server
from myo.ui.tmux.session import Session
from myo.ui.tmux.window import Window
from myo.ui.tmux.layout import Layout, LayoutDirections
from myo.ui.tmux.pane import Pane


class StateSpec(UnitSpec):

    @lazy
    def state(self):
        pane = Pane(id=Just(9), name='pan')
        lay = Layout(name='lay', panes=[pane])
        win = Window(name='vim', id=Just(0), root=lay)
        sess = Session(name='vim', id=Just(0), windows=[win])
        return TmuxState(server=Server(None), sessions=List(sess))

    def session_lens(self):
        s = (self.state.session_lens(__.has_ident('vim')) /
             __.modify(__.set(id=Just(1))))
        (s // _.sessions.head // _.id).should.contain(1)

    def window_lens(self):
        s = (self.state.window_lens(__.has_ident('vim')) /
             __.modify(__.set(id=Just(1))))
        (s // _.sessions.head // _.windows.head // _.id).should.contain(1)

    def layout_lens(self):
        h = LayoutDirections.horizontal
        s = (self.state.layout_lens(__.has_ident('lay')) /
             __.modify(__.set(direction=h)))
        dir = s // _.sessions.head // _.windows.head / _.root.direction
        dir.should.contain(h)

__all__ = ('StateSpec',)
