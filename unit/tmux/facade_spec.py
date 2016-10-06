from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.facade.main import TmuxFacade
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.window import Window
from myo.ui.tmux.session import Session
from myo.ui.tmux.pack import _normalize_weights, WindowPacker

from unit._support.spec import UnitSpec

from amino import Empty, List, Just, _, __
from amino.lazy import lazy


class TmuxFacadeSpec(UnitSpec):

    @lazy
    def state(self):
        pane = Pane(id=Just(9), name='pan')
        lay = Layout(name='lay', panes=[pane])
        par = Layout(name='par', layouts=[lay])
        win = Window(name='vim', id=Just(0), root=par)
        sess = Session(name='vim', id=Just(0), windows=[win])
        return TmuxState(sessions=List(sess))

    @lazy
    def tmux(self):
        return TmuxFacade(self.state, None)

    def layout_lens(self):
        name = 'new'
        s = self.state.layout_lens_ident('lay') / __.modify(__.set(name=name))
        l = s // _.sessions.head // _.windows.head // _.root.layouts.head
        (l / _.name).should.contain(name)

    def pane_lens(self):
        name = 'new'
        s = self.state.pane_lens_ident('pan') / __.modify(__.set(name=name))
        p = (s // _.sessions.head // _.windows.head // _.root.layouts.head //
             _.panes.head)
        (p / _.name).should.contain(name)

    def add_layout_to_layout(self):
        layout = Layout(name='lay2')
        s = self.tmux.add_layout_to_layout(Just('lay'), layout)
        l = (s // _.sessions.head // _.windows.head // _.root.layouts.head //
             _.layouts.head)
        l.should.contain(layout)

    def add_pane_to_layout(self):
        pane = Pane(name='pan2')
        s = self.tmux.add_pane_to_layout(Just('lay'), pane)
        p = (s // _.sessions.head // _.windows.head // _.root.layouts.head //
             _.panes.last)
        p.should.contain(pane)


class WindowPackerSpec(UnitSpec):

    @lazy
    def wp(self):
        return WindowPacker(None)

    def distribute(self):
        min_s = List(10, 0)
        max_s = List(99, 99)
        weights = List(Just(0), Empty())
        nw = _normalize_weights(weights)
        total = 50
        res = self.wp._distribute_sizes(min_s, max_s, nw, total)
        res.should.equal(List(10, 40))

    def cut(self):
        min_s = List(0, 50, 0, 50)
        weights = List(Empty(), Empty(), Empty(), Empty())
        nw = _normalize_weights(weights)
        total = 60
        res = self.wp._cut_sizes(min_s, nw, total)
        res.should.equal(List(0, 30, 0, 30))

    def balance_cut(self):
        min_s = List(0, 50, 0, 50)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.wp._balance_sizes(min_s, max_s, weights, total)
        res.should.equal(List(2, 28, 2, 28))

    def balance_dist(self):
        min_s = List(0, 10, 0, 10)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.wp._balance_sizes(min_s, max_s, weights, total)
        res.should.equal(List(10, 20, 10, 20))

__all__ = ('TmuxFacadeSpec',)
