from typing import Callable

from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane

from lenses import lens

from tryp import _, __

from trypnv.record import dfield, list_field, field


class Layout(View):
    name = field(str)
    flex = dfield(False)
    panes = list_field()
    layouts = list_field()

    def pane_index(self, f: Callable[[Pane], bool]):
        self.panes.index_where(f)

    def find_pane_deep(self, name):
        return (self.panes.find(_.name == name)
                .or_else(lambda: self._find_pane_in_layouts(name)))

    def _find_pane_in_layouts(self, name):
        return self.layouts.deep_find(__.find_pane(name))

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


class LayoutDirection():
    vertical = 0
    horizontal = 1


class LinearLayout(Layout):
    direction = dfield(LayoutDirection.vertical)


class VimLayout(LinearLayout):
    pass

__all__ = ('Layout', 'LinearLayout', 'LayoutDirection', 'VimLayout')
