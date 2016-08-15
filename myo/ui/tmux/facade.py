from typing import Tuple
from functools import singledispatch  # type: ignore
from operator import ne

from tryp.task import Task, task
from tryp.anon import L
from tryp import _, __, List, Left, F, Boolean, Right, Empty
from tryp.lazy import lazy

from myo.logging import Logging
from myo.ui.tmux.server import Server
from myo.ui.tmux.window import Window
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane, PaneAdapter
from myo.command import ShellCommand
from myo.ui.tmux.pane_path import PanePath


class LayoutFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.server = server
        self.panes = PaneFacade(server)

    def layout_open(self, layout):
        return (layout.layouts.exists(self.layout_open) or
                layout.panes.exists(self.panes.is_open))

    def view_open(self, view):
        f = (self.layout_open if isinstance(view, Layout) else
             self.panes.is_open)
        return f(view)

    def open_views(self, layout):
        return layout.views.filter(self.view_open)

    def open_pane(self, path: PanePath) -> Task[PanePath]:
        p = path.pane
        return (Task.now(Left('pane {} already open'.format(p)))
                if self.panes.is_open(p)
                else self._open_pane(path))

    def close_pane_path(self, path: PanePath):
        new_path = path.map_pane(__.set(id=Empty()))
        return self.panes.close(path.pane) / __.replace(new_path)

    def _open_pane(self, path) -> Task[PanePath]:
        return (
            self._open_in_layouts(path.pane, path.layout, path.outer)
            .map3(F(PanePath.create, path.window)) /
            Right
        )

    def _open_in_layouts(self, pane, layout, outer):
        if self.layout_open(layout):
            return self._open_in_layout(pane, layout) / (_ + (outer,))
        else:
            return (
                outer.detach_last.map2(F(self._open_in_layouts, pane)) |
                Task.failed('cannot open {} without open layout'.format(pane))
            ).map3(lambda p, l, o: (p, layout, o.cat(l)))

    def _ref_pane(self, layout):
        def go(l):
            return (self._opened_panes(l.panes).head
                    .or_else(l.layouts.find_map(go)))
        return (Task.call(go, layout) //
                L(Task.from_maybe)(_, "no ref pane for {}".format(layout)))

    def _open_in_layout(self, pane, layout) -> Task[Tuple[Layout, Pane]]:
        @task
        def open(ref):
            return (
                self.panes.find(ref) /
                __.split(layout.horizontal) /
                PaneAdapter /
                pane.open
            ) | pane
        return (self._ref_pane(layout) // open) & (Task.now(layout))

    def _opened_panes(self, panes):
        return panes.filter(self.panes.is_open)

    def pack_path(self, path: PanePath):
        return self.pack_window(path.window) / __.replace(path)

    def pack_window(self, window: Window):
        t = (
            Task.call(window.id.flat_map, self.server.window) //
            L(Task.from_maybe)(_, 'window not found: {}'.format(window)) /
            _.size
        )
        return t.flat_map2(L(self._pack_layout)(window.root, _, _)) / Right

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
            return (
                self._pack_layout(v, *sub_size)
                .flat_replace(
                    self._ref_pane(v) //
                    L(self._apply_size)(_, size, horizontal)
                )
            )
        views = self.open_views(l)
        count = views.length
        if count > 0:
            # each pane spacer takes up one cell
            m = self._measure_layout(views, total - count + 1)
            return views.zip(m).map2(recurse).sequence(Task)
        else:
            return Task.now(List())

    def _measure_layout(self, views, total):
        calc = lambda s: s if s > 1 else s * total
        min_s = self.actual_min_sizes(views) / calc
        max_s = self.actual_max_sizes(views) / calc
        weights = self.weights(views)
        return (self._cut_sizes(min_s, weights, total) if sum(min_s) > total
                else self._distribute_sizes(min_s, max_s, weights, total))

    def _cut_sizes(self, min_s, weights, total):
        surplus = sum(min_s) - total
        dist = weights / (1 - _) / (surplus * _)
        return (min_s & dist).map2(_ - _)

    def _distribute_sizes(self, min_s, max_s, weights, total):
        count = max_s.length
        surplus = total - sum(min_s)
        sizes1 = min_s.zip(max_s, weights).map3(
            lambda l, h, w: min(l + w * surplus, h))
        rest = total - sum(sizes1)
        unsat = (max_s & sizes1).map2(ne) / Boolean
        unsat_left = count - sum(unsat / _.value) > 0
        def trim_weights():
            w1 = (unsat & weights).map2(lambda s, w: s.maybe(w))
            return self._normalize_weights(w1)
        def dist_rest():
            rest_w = trim_weights() if unsat_left else weights
            return (sizes1 & rest_w).map2(lambda a, w: a + w * rest)
        return sizes1 if rest <= 0 else dist_rest()

    def _apply_size(self, pane, size, horizontal):
        return (
            Task.call(self.panes.find, pane) //
            L(Task.from_maybe)(_, 'pane not found: {}'.format(pane)) //
            __.resize(size, horizontal)
        )

    def actual_min_sizes(self, views):
        return views / (lambda a: a.fixed_size.or_else(a.min_size) | 0)

    def actual_max_sizes(self, views):
        return views / (lambda a: a.fixed_size.or_else(a.max_size) | 999)

    def weights(self, views):
        return self._normalize_weights(views / _.effective_weight)

    def _normalize_weights(self, weights):
        amended = self._amend_weights(weights)
        total = sum(amended)
        total1 = 1 if total == 0 else total
        return amended / (_ / total1)

    def _amend_weights(self, weights):
        total = sum(weights.join)
        total1 = 1 if total == 0 else total
        empties = weights.filter(_.is_empty).length
        empties1 = 1 if empties == 0 else empties
        empty = total1 / empties1
        return weights / (_ | empty)


class PaneFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.server = server

    @lazy
    def panes(self):
        return self.server.panes

    @lazy
    def pane_data(self):
        return self.server.pane_data

    @lazy
    def pane_ids(self):
        return self.pane_data // _.id_i.to_list

    def is_open(self, pane):
        return pane.id.exists(self.pane_ids.contains)

    def find_by_id(self, id):
        return self.panes.find(__.id_i.contains(id))

    def find_by_name(self, name):
        return self.panes.find(_.name == name)

    def select_pane(self, session_id, window_id, pane_id):
        return (
            self.server.session_by_id(session_id) //
            __.window_by_id(window_id) //
            __.pane_by_id(pane_id)
        )

    def find(self, pane: Pane) -> PaneAdapter:
        def find_by_id(pane_id):
            return (
                (pane.session_id & pane.window_id)
                .flat_map2(L(self.select_pane)(_, _, pane_id))
                .or_else(L(self.find_by_id)(pane_id))
            )
        return pane.id // find_by_id

    def _find_task(self, pane: Pane) -> Task[PaneAdapter]:
        return (
            Task.call(self.find, pane) //
            L(Task.from_maybe)(_, 'pane not found')
        )

    def run_command(self, pane: Pane, command: ShellCommand):
        return self.run_command_line(pane, command.line)

    def run_command_line(self, pane: Pane, line: str):
        return (
            self._find_task(pane) /
            __.send_keys(line, suppress_history=False)
        )

    def command_pid(self, pane: Pane):
        return self._find_task(pane) / _.command_pid

    def close(self, pane: Pane):
        err = 'cannot close pane {}: not found'.format(pane)
        return (Task.call(self.find, pane) //
                __.cata(__.kill.map(Right), lambda: Task.now(Left(err))))

    def close_id(self, id: int):
        return self.server.cmd('kill-pane', '-t', '%{}'.format(id))

    def ensure_not_running(self, pane: Pane):
        return (
            self._find_task(pane) /
            __.not_running.either('command already running', True)
        )

__all__ = ('LayoutFacade', 'PaneFacade')
