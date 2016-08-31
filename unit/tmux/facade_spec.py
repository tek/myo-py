from myo.ui.tmux.facade import LayoutFacade

from unit._support.spec import TmuxUnitSpec

from amino import Empty, List, Just


class LayoutFacadeSpec(TmuxUnitSpec):

    def setup(self):
        super().setup()
        self.f = LayoutFacade(self.server)

    def distribute(self):
        min_s = List(10, 0)
        max_s = List(99, 99)
        weights = List(Just(0), Empty())
        nw = self.f._normalize_weights(weights)
        total = 50
        res = self.f._distribute_sizes(min_s, max_s, nw, total)
        res.should.equal(List(10, 40))

    def cut(self):
        min_s = List(0, 50, 0, 50)
        weights = List(Empty(), Empty(), Empty(), Empty())
        nw = self.f._normalize_weights(weights)
        total = 60
        res = self.f._cut_sizes(min_s, nw, total)
        res.should.equal(List(0, 30, 0, 30))

    def balance_cut(self):
        min_s = List(0, 50, 0, 50)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.f._balance_sizes(min_s, max_s, weights, total)
        res.should.equal(List(2, 28, 2, 28))

    def balance_dist(self):
        min_s = List(0, 10, 0, 10)
        max_s = List(50, 50, 50, 50)
        weights = List(0.25, 0.25, 0.25, 0.25)
        total = 60
        res = self.f._balance_sizes(min_s, max_s, weights, total)
        res.should.equal(List(10, 20, 10, 20))

__all__ = ('LayoutFacadeSpec',)
