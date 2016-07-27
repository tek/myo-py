from typing import Callable, Tuple

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
                __.native.split_window() /
                _._pane_id /
                parse_pane_id |
                Empty()
            )
            return pane.set(id=new.to_maybe), layout
        return self._ref_pane(layout) // go

    def _opened_panes(self, panes):
        return panes.filter(self.pane_open)

    def pack_path(self, path: PanePath):
        self._measure_layout(None)
        return Task.call(self._measure_layout, path.layout) / (lambda a: path)

    def _pack_layout(self, l):
        return l

    def _measure_layout(self, l):
        ''' analyze max/min sizes etc. and create List[Measure] of
        actual sizes
        must be executed top-down, as sizes of layouts are transient due
        to the possibility of manual changes
        '''
        pass


__all__ = ('PanePath', 'LayoutHandler')
