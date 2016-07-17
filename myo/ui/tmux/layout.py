from typing import Callable, Tuple

from myo.ui.tmux.view import View
from myo.ui.tmux.pane import Pane, parse_id
from myo.logging import Logging
from myo.ui.tmux.server import Server

from lenses import lens

from tryp import _, __, List, Either, Left, F, Just, Empty
from tryp.task import Task, task

from trypnv.record import dfield, maybe_field, list_field, field, Record


class Layout(View):
    name = field(str)
    flex = dfield(False)
    min_size = dfield(0)
    max_size = maybe_field(int)
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


class PanePath(Record):
    pane = field(Pane)
    layout = field(Layout)
    outer = list_field()

    @staticmethod
    def create(pane, layout, outer):
        return PanePath(pane=pane, layout=layout, outer=outer)

    @staticmethod
    def try_create(views: List[View]) -> Either[str, 'PanePath']:
        def try_create1(pane, layouts):
            return (
                layouts.detach_last.map2(F(PanePath.create, pane))
                .to_either('PanePath.create: last item is not Pane')
            )
        return (
            views.detach_last.map2(try_create1) |
            Left('PanePath.create: empty List[View]')
        )

    @property
    def to_list(self):
        return self.outer + List(self.layout, self.pane)


class LayoutHandler(Logging):

    def __init__(self, server: Server) -> None:
        self.server = server

    def pane_open(self, pane):
        return pane.id_s.exists(self.server.pane_ids.contains)

    def layout_open(self, layout):
        return (layout.layouts.exists(self.layout_open) or
                layout.panes.exists(self.pane_open))

    def open_pane(self, path: PanePath) -> Task[PanePath]:
        return (Task.now(path) if self.pane_open(path.pane) else
                self._open_pane(path))

    def _open_pane(self, path) -> Task[PanePath]:
        return (self._open_in_layouts(path.pane, path.layout, path.outer)
                .map3(PanePath.create))

    def _open_in_layouts(self, pane, layout, outer):
        if self.layout_open(layout):
            return self._open_in_layout(pane, layout) / (_ + (outer,))
        else:
            ret = (
                outer.detach_last.map2(F(self._open_in_layouts, pane)) |
                Task.failed('cannot open {} without open layout'.format(pane))
            )
            return ret / (lambda p, l, o: (p, layout, o.cat(l)))

    def _ref_pane(self, layout):
        def go(l):
            return (self._opened_panes(l.panes).head
                    .or_else(l.layouts.find_map(go)))
        return (Task.call(go, layout) //
                F(Task.from_maybe, error="no ref pane for {}".format(layout)))

    def _open_in_layout(self, pane, layout) -> Task[Tuple[Layout, Pane]]:
        @task
        def go(ref):
            new = (ref.id // self.server.find_pane_by_id /
                   __.native.split_window() / _._pane_id / parse_id | Empty())
            return pane.set(id=new.to_maybe), layout
        return self._ref_pane(layout) // go

    def _opened_panes(self, panes):
        return panes.filter(self.pane_open)

__all__ = ('Layout', 'LinearLayout', 'LayoutDirection', 'VimLayout',
           'PanePath', 'LayoutHandler')
