from typing import Callable, Tuple
from functools import singledispatch  # type: ignore

from tryp.task import Task, task
from tryp.anon import L
from tryp import _, __, List, Either, Left, F, Empty

from trypnv.record import list_field, field, Record

from myo.logging import Logging
from myo.ui.tmux.server import Server
from myo.ui.tmux.window import Window
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane, parse_pane_id
from myo.ui.tmux.view import View


class PanePath(Record):
    window = field(Window)
    pane = field(Pane)
    layout = field(Layout)
    outer = list_field()

    @staticmethod
    def create(window, pane, layout, outer):
        return PanePath(window=window, pane=pane, layout=layout, outer=outer)

    @staticmethod
    def try_create(win: Window, views: List[View]) -> Either[str, 'PanePath']:
        def try_create1(pane, layouts):
            return (
                layouts.detach_last.map2(F(PanePath.create, win, pane))
                .to_either('PanePath.create: last item is not Pane')
            )
        return (
            views.detach_last.map2(try_create1) |
            Left('PanePath.create: empty List[View]')
        )

    @property
    def layouts(self):
        return self.outer.cat(self.layout)

    @property
    def to_list(self):
        return self.layouts.cat(self.pane)

    def map(self, fp: Callable[[Pane], Pane], fl: Callable[[Layout], Layout]):
        return PanePath.create(
            self.window, fp(self.pane), fl(self.layout), self.outer / fl)


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
        return (
            self._open_in_layouts(path.pane, path.layout, path.outer)
            .map3(F(PanePath.create, path.window))
        )

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
                L(Task.from_maybe)(_, "no ref pane for {}".format(layout)))

    def _open_in_layout(self, pane, layout) -> Task[Tuple[Layout, Pane]]:
        @task
        def go(ref):
            new = (
                ref.id //
                self.server.find_pane_by_id /
                __.split(layout.horizontal) /
                _._pane_id /
                parse_pane_id |
                Empty()
            )
            return pane.set(id=new.to_maybe), layout
        return self._ref_pane(layout) // go

    def _opened_panes(self, panes):
        return panes.filter(self.pane_open)

    def pack_path(self, path: PanePath):
        return self.pack_window(path.window) / (lambda a: path)

    def pack_window(self, window: Window):
        t = (
            Task.call(self.server.window, window.id) //
            L(Task.from_maybe)(_, 'window not found: {}'.format(window)) /
            _.size
        )
        return t.flat_map2(L(self._pack_layout)(window.root, _, _))

    def _pack_layout(self, l, w, h):
        horizontal = l.horizontal
        total = w if horizontal else h
        @singledispatch
        def recurse(v, size):
            pass
        @recurse.register(Pane)
        def rec_pane(v, size):
            return self._apply_size(v, size, horizontal)
        @recurse.register(Layout)
        def rec_layout(v, size):
            sub_size = (size, h) if horizontal else (w, size)
            return self._pack_layout(v, *sub_size)
        m = self._measure_layout(l, total)
        return l.views.zip(m).map2(recurse).sequence(Task)

    def _measure_layout(self, l, total):
        calc = lambda s: s if s > 1 else s * total
        min_s = l.actual_min_sizes / calc
        max_s = l.actual_max_sizes / calc
        return (self._cut_sizes(min_s, l.weights, total) if sum(min_s) > total
                else self._distribute_sizes(min_s, max_s, l.weights, total))

    def _cut_sizes(self, min_s, weights, total):
        surplus = sum(min_s) - total
        if weights.flatten.empty:
            equi = surplus / min_s.length
            return min_s / (_ - equi)
        else:
            dist = weights / (_ / (lambda a: surplus * (1 - a)) | 0)
            return min_s.zip(dist).map2(_ - _)

    def _distribute_sizes(self, min_s, max_s, weights, total):
        return min_s

    def _apply_size(self, pane, size, horizontal):
        return (
            Task.call(pane.id.flat_map, self.server.pane) //
            L(Task.from_maybe)(_, 'pane not found: {}'.format(pane)) //
            __.resize(size, horizontal)
        )

__all__ = ('PanePath', 'LayoutHandler')
