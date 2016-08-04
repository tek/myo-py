from typing import Callable

from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane

from lenses import lens

from tryp import _, __, List
from tryp.lazy import lazy

from trypnv.record import dfield, list_field, field, Record


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
    name = field(str)
    panes = list_field()
    layouts = list_field()
    direction = dfield(LayoutDirections.vertical)

    def pane_index(self, f: Callable[[Pane], bool]):
        self.panes.index_where(f)

    def find_pane_deep(self, name):
        return (self.panes.find(_.name == name)
                .or_else(lambda: self._find_pane_in_layouts(name)))

    def _find_pane_in_layouts(self, name):
        return self.layouts.find_map(__.find_pane_deep(name))

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
        total = sum(w.flatten)
        return w / (lambda a: a / (_ / total))

    @lazy
    def actual_min_sizes(self):
        return self.views / (lambda a: a.fixed_size.or_else(a.min_size) | 0)

    @lazy
    def actual_max_sizes(self):
        return self.views / (lambda a: a.fixed_size.or_else(a.max_size) | 999)



    pass
class VimLayout(Layout):

__all__ = ('Layout', 'LayoutDirection', 'VimLayout')
