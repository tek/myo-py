from typing import Callable, Any

from amino.task import Task

from lenses import Lens, lens
from amino import Either, List, F, _, L, Left, __, Right, I
from amino.lens.tree import path_lens_unbound_pre

from ribosome.record import Record, field, list_field
from ribosome.machine import Message
from ribosome.machine.transition import Error

from myo.ui.tmux.window import Window
from myo.logging import Logging
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
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
    def try_create(views: List[View]) -> Either[str, 'PanePath']:
        def try_create2(pane, win, layouts):
            return (
                layouts.detach_last.map2(F(PanePath.create, win, pane))
                .to_either('PanePath.create: last item is not Pane')
            )
        def try_create1(pane, layouts):
            return (
                layouts.detach_head
                .to_either('PanePath.create: last item is not Pane')
                .flat_map2(F(try_create2, pane))
            )
        return (
            views.detach_last.to_either('PanePath.create: empty List[View]')
            .flat_map2(try_create1)
        )

    @property
    def layouts(self):
        return self.outer.cat(self.layout)

    @property
    def to_list(self):
        return self.layouts.cat(self.pane).cons(self.window)

    def map(self, fp: Callable[[Pane], Pane], fl: Callable[[Layout], Layout]):
        return PanePath.create(
            self.window, fp(self.pane), fl(self.layout), self.outer / fl)

    def map_pane(self, f: Callable[[Pane], Pane]):
        return self.map(f, I)

PPTrans = Callable[[PanePath], Task[Either[Any, PanePath]]]


class PanePathLens(Record):
    lens = field(Lens)

    @staticmethod
    def create(lens: Lens):
        return PanePathLens(lens=lens)

    def run(self, win: Window, f: PPTrans) -> Task[Either[Any, Window]]:
        bound = self.lens.bind(win)
        path = PanePath.try_create(List.wrap(bound.get()))
        def update(pp):
            return bound.set(pp.to_list)
        def apply(pp):
            return f(pp) / (_ / update)
        return Task.from_either(path) // apply


def _initial_ppm_f(pp, window) -> Task[Either[Any, Window]]:
    return Task.now(Right(window))


class PanePathMod(Logging, Message):
    pred = field(Callable)
    _f = field(Callable, initial=(lambda: _initial_ppm_f))

    def _chain(self, f: PPTrans, g: Callable):
        h = lambda pp: L(pp.run)(_, f)
        chain = lambda pp, win: self._f(pp, win) // g(win, h(pp))
        return PanePathMod(pred=self.pred, _f=chain)

    def map(self, f: PPTrans) -> Task[Either[Any, Window]]:
        keep_error = F(Left) >> Task.now
        return self._chain(f, lambda w, d: __.cata(keep_error, d))

    __truediv__ = map

    def and_then(self, f: PPTrans):
        return self._chain(f, lambda w, d: lambda a: d(a | w))

    __add__ = and_then

    def run(self, window: Window) -> Task:
        return self._lens(window) // L(self._f)(_, window)

    def _lens(self, window):
        f = __.panes.find_lens_pred(self.pred).map(lens().panes.add_lens)
        sub = _.layouts
        pre = _.root
        return (
            Task.from_maybe(
                path_lens_unbound_pre(window, sub, f, pre),
                Error('lens path failed for {}'.format(self.pred))
            ) /
            PanePathLens.create
        )


def ppm_id(path: PanePathMod):
    return Task.now(Right(path))

__all__ = ('PanePath', 'PanePathLens', 'PanePathMod', 'ppm_id')
