from typing import Callable, Any

from amino.task import Task

from lenses import Lens, lens
from amino import Either, List, F, _, L, Left, __, Right, I, Just, Boolean
from amino.lens.tree import path_lens_unbound

from ribosome.record import field, list_field, map_field
from ribosome.machine import Message

from myo.ui.tmux.window import Window
from myo.logging import Logging
from myo.ui.tmux.view import View
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.session import Session
from myo.ui.tmux.data import TmuxState
from myo.record import Record


class ViewPath(Record):
    session = field(Session)
    window = field(Window)
    view = field(View)
    layout = field(Layout)
    outer = list_field()

    @staticmethod
    def create(session, window, view, layout, outer):
        return ViewPath(session=session, window=window, view=view,
                        layout=layout, outer=outer)

    @staticmethod
    def try_create(session: Session, window: Window, views: List[View]
                   ) -> Either[str, 'ViewPath']:
        def try_create1(view, layouts):
            return (
                layouts.detach_last
                .to_either('ViewPath.create: only two items in views')
                .map2(L(ViewPath.create)(session, window, view, _, _))
            )
        return (
            views.detach_last.to_either('ViewPath.create: empty List[View]')
            .flat_map2(try_create1)
        )

    @property
    def layouts(self):
        return self.outer.cat(self.layout)

    @property
    def view_list(self):
        return self.layouts.cat(self.view)

    def map(self, fp: Callable[[View], View], fl: Callable[[Layout], Layout]):
        return ViewPath.create(
            self.session, self.window, fp(self.view), fl(self.layout),
            self.outer / fl
        )

    def map_view(self, f: Callable[[View], View]):
        return self.map(f, I)

    @property
    def is_pane(self):
        return Boolean(isinstance(self.view, Pane))

    @property
    def loc(self):
        return ViewLoc.create(self.session, self.window, self.view)

PPTrans = Callable[[ViewPath], Task[Either[Any, ViewPath]]]


class ViewPathLens(Record):
    lens = field(Lens)

    @staticmethod
    def create(lens: Lens):
        return ViewPathLens(lens=lens)

    def _check_result_type(self, result):
        if (
                not isinstance(result, Either) or (
                    result.is_right and
                    not result.exists(L(isinstance)(_, ViewPath))
                )
        ):
            msg = ('invalid ViewPath transition result type, must be' +
                   ' Either[..., ViewPath]: {}')
            raise Exception(msg.format(result))

    def run(self, state: TmuxState, f: PPTrans) -> Task[Either[Any, Window]]:
        bound = self.lens.bind(state)
        session, (window, views) = bound.get()
        path = ViewPath.try_create(session, window, List.wrap(views))
        set = lambda a: bound.set((session, (window, a)))
        def result(r):
            self._check_result_type(r)
            return r / _.view_list / set
        return Task.from_either(path) // F(f) / result


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
        h = lambda vp: L(vp.run)(_, f)
        chain = lambda vp, win: self._f(vp, win) // g(win, h(vp))
        return type(self)(pred=self.pred, _f=chain)  # type: ignore

    def map(self, f: PPTrans) -> Task[Either[Any, Window]]:
        keep_error = F(Left) >> Task.now
        return self._chain(f, lambda w, d: __.cata(keep_error, d))

    __truediv__ = map

    def and_then(self, f: PPTrans):
        return self._chain(f, lambda w, d: lambda a: d(a | w))

    __add__ = and_then

    def foreach(self, f: PPTrans):
        run = lambda path: f(path).replace(Right(path))
        return self.map(run)

    __mod__ = foreach

    def run(self, state: TmuxState) -> Task:
        return self._lens(state) // L(self._f)(_, state)

    def _lens(self, state):
        err = 'view lens path failed for {}'.format(self.pred)
        def main_lens(w):
            return ((Just(lens()) &
                     path_lens_unbound(w.root, _.layouts, self.attr)
                     .map(lens().root.add_lens)
                     )
                    .map2(lens().tuple_))
        def s_lens(s):
            return ((Just(lens()) & s.attr_lens(_.windows, main_lens))
                    .map2(lens().tuple_))
        st_lens = state.attr_lens(_.sessions, s_lens)
        return Task.from_maybe(st_lens, err) / ViewPathLens.create


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


class ViewLoc(Record):
    view = field(View)
    window = field(Window)
    session = field(Session)

    @staticmethod
    def create(session, window, view):
        return ViewLoc(view=view, window=window, session=session)

    @property
    def _str_extra(self):
        return List(self.session, self.window, self.view)

    def with_view(self, v: View):
        return self.set(view=v)


class LayoutLoc(ViewLoc):
    view = field(Layout)

__all__ = ('ViewPath', 'ViewPathLens', 'ViewPathMod', 'ppm_id')
