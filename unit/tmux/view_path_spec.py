from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.window import Window
from myo.ui.tmux.view_path import ppm_id, PanePathMod

from unit._support.spec import UnitSpec

from amino import List, __, _


class ViewPathSpec(UnitSpec):

    def path(self):
        n1 = List.random_string()
        n2 = List.random_string()
        pane = Pane(name=n1)
        l = Layout(name='l1', layouts=List(Layout(name='l2',
                                                  panes=List(pane))))
        win = Window(name='root', root=l)
        mod = lambda p: ppm_id(p.map_view(__.set(name=n2)))
        ppm = PanePathMod(pred=__.has_ident(n1)) / mod
        t = ppm.run(win)
        w = t.attempt().join | None
        n = w.root.layouts.head // _.panes.head / _.name
        n.should.contain(n2)

__all__ = ('ViewPathSpec',)
