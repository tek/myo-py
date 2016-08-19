from typing import Callable

from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.util import Ident

from lenses import lens

from amino import _, __, List
from amino.lazy import lazy

from ribosome.record import dfield, list_field, field, Record


class LayoutDirection(Record):
    id = field(str)


class LayoutDirections:
    vertical = LayoutDirection(id='vertical')
    horizontal = LayoutDirection(id='horizontal')
    all = List(vertical, horizontal)
    all_ids = all / _.id  # type: List[str]

    @staticmethod
    def parse(s: str):
        return (LayoutDirections.horizontal if s == 'horizontal' else
                LayoutDirections.vertical)


class Layout(View):
    panes = list_field()
    layouts = list_field()
    direction = dfield(LayoutDirections.vertical)

    def pane_index(self, f: Callable[[Pane], bool]):
        self.panes.index_where(f)

    def find_pane_pred(self, pred: Callable[[Pane], bool]):
        return (self.panes.find(pred)
                .or_else(lambda: self._find_pane_in_layouts(pred)))

    def _find_pane_in_layouts(self, pred: Callable[[Pane], bool]):
        return self.layouts.find_map(__.find_pane_pred(pred))

    def find_pane(self, ident: Ident):
        return self.find_pane_pred(__.has_ident(ident))

    @staticmethod
    def pane_lens(root, f: Callable[[Pane], bool]):
        def g(l):
            return (
                l.panes.lens(f)
                .map(lens().panes.add_lens)
                .or_else(lambda: h(l))
            )
        def h(l):
            return l.layouts.deep_lens(g) / lens().layouts.add_lens
        return h(root) / lens(root).add_lens

    @lazy
    def views(self):
        return self.panes + self.layouts

    @lazy
    def horizontal(self):
        return self.direction == LayoutDirections.horizontal

    @lazy
    def weights(self):
        w = self.views / _.weight
        total = sum(w.join)
        return w / (lambda a: a / (_ / total))

    @lazy
    def actual_min_sizes(self):
        return self.views / (lambda a: a.fixed_size.or_else(a.min_size) | 0)

    @lazy
    def actual_max_sizes(self):
        return self.views / (lambda a: a.fixed_size.or_else(a.max_size) | 999)

    @property
    def desc(self):
        dir = 'H' if self.horizontal else 'V'
        return 'L {} \'{}\' {}'.format(dir, self.name, self.size_desc)

    @property
    def all_panes(self):
        return self.panes + (self.layouts // _.all_panes)


class VimLayout(Layout):

    @property
    def desc(self):
        return 'V{}'.format(super().desc)

__all__ = ('Layout', 'LayoutDirection', 'VimLayout')
