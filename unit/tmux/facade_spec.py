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

__all__ = ('LayoutFacadeSpec',)
