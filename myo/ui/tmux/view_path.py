from typing import Callable, Any

from amino.task import Task

from lenses import Lens, lens
from amino import Either, List, F, _, L, Left, __, Right, I
from amino.lens.tree import path_lens_unbound_pre

from ribosome.record import Record, field, list_field, map_field
from ribosome.machine import Message
from ribosome.machine.transition import Fatal

from myo.ui.tmux.window import Window
from myo.logging import Logging
from myo.ui.tmux.view import View
from myo.ui.tmux.layout import Layout


class ViewPath(Record):
    window = field(Window)
    view = field(View)
    layout = field(Layout)
    outer = list_field()

    @staticmethod
    def create(window, view, layout, outer):
        return ViewPath(window=window, view=view, layout=layout, outer=outer)

    @staticmethod
    def try_create(views: List[View]) -> Either[str, 'ViewPath']:
        def try_create2(view, win, layouts):
            return (
                layouts.detach_last.map2(F(ViewPath.create, win, view))
                .to_either('ViewPath.create: last item is not View')
            )
        def try_create1(view, layouts):
            return (
                layouts.detach_head
                .to_either('ViewPath.create: last item is not View')
                .flat_map2(F(try_create2, view))
            )
        return (
            views.detach_last.to_either('ViewPath.create: empty List[View]')
            .flat_map2(try_create1)
        )

    @property
    def layouts(self):
        return self.outer.cat(self.layout)

    @property
    def to_list(self):
        return self.layouts.cat(self.view).cons(self.window)

    def map(self, fp: Callable[[View], View], fl: Callable[[Layout], Layout]):
        return ViewPath.create(
            self.window, fp(self.view), fl(self.layout), self.outer / fl)

    def map_view(self, f: Callable[[View], View]):
        return self.map(f, I)

PPTrans = Callable[[ViewPath], Task[Either[Any, ViewPath]]]


class ViewPathLens(Record):
    lens = field(Lens)

    @staticmethod
    def create(lens: Lens):
        return ViewPathLens(lens=lens)

    def run(self, win: Window, f: PPTrans) -> Task[Either[Any, Window]]:
        bound = self.lens.bind(win)
        path = ViewPath.try_create(List.wrap(bound.get()))
        apply = F(f) / (_ / _.to_list / bound.set)
        return Task.from_either(path) // apply


def _initial_ppm_f(pp, window) -> Task[Either[Any, Window]]:
    return Task.now(Right(window))


class ViewPathMod(Logging, Message):
    pred = field(Callable)
    _f = field(Callable, initial=(lambda: _initial_ppm_f))
    options = map_field()

    @property
    def attr(self):
        return (lambda a: self._pane_attr(a).or_else(self._layout_attr(a)))

    @property
    def _pane_attr(self):
        return self._attr(_.panes)

    @property
    def _layout_attr(self):
        return self._attr(_.layouts)

    def _attr(self, f):
        return (
            f(__)
            .find_lens_pred(self.pred)
            .map(f(lens()).add_lens)
        )

    def _chain(self, f: PPTrans, g: Callable):
        h = lambda pp: L(pp.run)(_, f)
        chain = lambda pp, win: self._f(pp, win) // g(win, h(pp))
        return type(self)(pred=self.pred, _f=chain)  # type: ignore

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
        sub = _.layouts
        pre = _.root
        return (
            Task.from_maybe(
                path_lens_unbound_pre(window, sub, self.attr, pre),
                Fatal('lens path failed for {}'.format(self.pred))
            ) /
            ViewPathLens.create
        )


class PanePathMod(ViewPathMod):

    @property
    def attr(self):
        return self._pane_attr


class LayoutPathMod(ViewPathMod):

    @property
    def attr(self):
        return self._layout_attr


def ppm_id(path: ViewPathMod):
    return Task.now(Right(path))

__all__ = ('ViewPath', 'ViewPathLens', 'ViewPathMod', 'ppm_id')
