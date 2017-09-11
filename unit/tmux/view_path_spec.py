from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.window import Window
from myo.ui.tmux.view_path import ppm_id, PanePathMod
from myo.ui.tmux.session import Session
from myo.ui.tmux.data import TmuxState

from unit._support.spec import UnitSpec

from kallikrein import k, Expectation
from kallikrein.matchers import contain

from amino import List, __, _
from amino.lazy import lazy


class ViewPathSpec(UnitSpec):
    '''view path
    modify the name of a pane with a `PanePathMod` $path
    '''

    @lazy
    def n1(self) -> List[str]:
        return List.random_string()

    @lazy
    def n2(self) -> List[str]:
        return List.random_string()

    @lazy
    def pane(self) -> Pane:
        return Pane(name=self.n1)

    @lazy
    def lay(self) -> Layout:
        return Layout(name='l1', layouts=List(Layout(name='l2', panes=List(self.pane))))

    @lazy
    def win(self) -> Window:
        return Window(name='root', root=self.lay)

    @lazy
    def state(self) -> TmuxState:
        sess = Session(name='sess', windows=[self.win])
        return TmuxState(sessions=List(sess))

    def path(self) -> Expectation:
        mod = lambda p: ppm_id(p.map_view(__.set(name=self.n2)))
        ppm = PanePathMod(pred=__.has_ident(self.n1)) / mod
        t = ppm.run(self.state)
        s = t.attempt.join
        n = s // (lambda a: a.sessions[0].windows[0].root.layouts.head) // _.panes.head / _.name
        return k(n).must(contain(self.n2))

__all__ = ('ViewPathSpec',)
