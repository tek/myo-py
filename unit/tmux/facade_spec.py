from myo.ui.tmux.data import TmuxState
from myo.ui.tmux.facade.main import TmuxFacade
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.window import Window
from myo.ui.tmux.session import Session
from myo.ui.tmux.pack import _normalize_weights, WindowPacker

from unit._support.spec import UnitSpec

from kallikrein import Expectation, k
from kallikrein.matchers import contain

from amino import Empty, List, Just, _, __
from amino.lazy import lazy


class TmuxFacadeSpec(UnitSpec):
    '''tmux facade

    acesss tmux state data via lenses
    layout $layout_lens
    pane $pane_lens

    add views to layouts
    layout $add_layout_to_layout
    pane $add_pane_to_layout
    '''

    @lazy
    def state(self) -> TmuxState:
        pane = Pane(id=Just(9), name='pan')
        lay = Layout(name='lay', panes=[pane])
        par = Layout(name='par', layouts=[lay])
        win = Window(name='vim', id=Just(0), root=par)
        sess = Session(name='vim', id=Just(0), windows=[win])
        return TmuxState(sessions=List(sess))

    @lazy
    def tmux(self) -> TmuxFacade:
        return TmuxFacade(self.state, None)

    def layout_lens(self) -> Expectation:
        name = 'new'
        s = self.state.layout_lens_ident('lay') / __.modify(__.set(name=name))
        l = s // _.sessions.head // _.windows.head // _.root.layouts.head
        return k(l / _.name).must(contain(name))

    def pane_lens(self) -> Expectation:
        name = 'new'
        s = self.state.pane_lens_ident('pan') / __.modify(__.set(name=name))
        p = s // _.sessions.head // _.windows.head // _.root.layouts.head // _.panes.head
        return k(p / _.name).must(contain(name))

    def add_layout_to_layout(self) -> Expectation:
        layout = Layout(name='lay2')
        s = self.tmux.add_layout_to_layout(Just('lay'), layout)
        l = s // _.sessions.head // _.windows.head // _.root.layouts.head // _.layouts.head
        return k(l).must(contain(layout))

    def add_pane_to_layout(self) -> Expectation:
        pane = Pane(name='pan2')
        s = self.tmux.add_pane_to_layout(Just('lay'), pane)
        p = s // _.sessions.head // _.windows.head // _.root.layouts.head // _.panes.last
        return k(p).must(contain(pane))


class WindowPackerSpec(UnitSpec):
    '''window packer
    distribute sizes $distribute
    cut sizes $cut
    cut and balance sizes $balance_cut
    distribute and balance sizes $balance_dist
    '''

    @lazy
    def wp(self) -> WindowPacker:
        return WindowPacker(None)

    def distribute(self) -> Expectation:
        min_s = List(10, 0)
        max_s = List(99, 99)
        weights = List(Just(0), Empty())
        nw = _normalize_weights(weights)
        total = 50
        res = self.wp._distribute_sizes(min_s, max_s, nw, total)
        return k(res) == List(10, 40)

    def cut(self) -> Expectation:
        min_s = List(0, 50, 0, 50)
        weights = List(Empty(), Empty(), Empty(), Empty())
        nw = _normalize_weights(weights)
        total = 60
        res = self.wp._cut_sizes(min_s, nw, total)
        return k(res) == List(0, 30, 0, 30)

    def balance_cut(self) -> Expectation:
        min_s = List(0, 50, 0, 50)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.wp._balance_sizes(min_s, max_s, weights, total)
        return k(res) == List(2, 28, 2, 28)

    def balance_dist(self) -> Expectation:
        min_s = List(0, 10, 0, 10)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.wp._balance_sizes(min_s, max_s, weights, total)
        return k(res) == List(10, 20, 10, 20)

__all__ = ('TmuxFacadeSpec', 'WindowPackerSpec')
