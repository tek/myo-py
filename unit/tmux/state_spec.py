from unit._support.spec import UnitSpec

from amino import List, Just, __, _

from kallikrein.matchers import contain
from kallikrein import k, Expectation
from amino.lazy import lazy

from myo.components.tmux.main import TmuxState
from myo.ui.tmux.session import Session
from myo.ui.tmux.window import Window
from myo.ui.tmux.layout import Layout, LayoutDirections
from myo.ui.tmux.pane import Pane


class StateSpec(UnitSpec):
    '''tmux state
    access data with lenses
    a session $session_lens
    a window $window_lens
    a layout $layout_lens
    '''

    @lazy
    def state(self) -> TmuxState:
        pane = Pane(id=Just(9), name='pan')
        lay = Layout(name='lay', panes=[pane])
        win = Window(name='vim', id=Just(0), root=lay)
        sess = Session(name='vim', id=Just(0), windows=[win])
        return TmuxState(sessions=List(sess))

    def session_lens(self) -> Expectation:
        s = (self.state.session_lens(__.has_ident('vim')) /
             __.modify(__.set(id=Just(1))))
        return k(s // _.sessions.head // _.id).must(contain(1))

    def window_lens(self) -> Expectation:
        s = (self.state.window_lens(__.has_ident('vim')) /
             __.modify(__.set(id=Just(1))))
        return k(s // _.sessions.head // _.windows.head // _.id).must(contain(1))

    def layout_lens(self) -> Expectation:
        h = LayoutDirections.horizontal
        s = (self.state.layout_lens(__.has_ident('lay')) /
             __.modify(__.set(direction=h)))
        dir = s // _.sessions.head // _.windows.head / _.root.direction
        return k(dir).must(contain(h))

__all__ = ('StateSpec',)
