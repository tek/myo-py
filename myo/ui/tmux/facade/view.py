import time
import signal
from typing import Tuple
from functools import singledispatch  # type: ignore
from operator import ne, sub

from psutil import Process

from amino.task import Task, task
from amino.anon import L
from amino import _, __, List, Left, F, Boolean, Right, Empty, Either, Maybe, I
from amino.lazy import lazy

from ribosome.machine.transition import Fatal, NothingToDo
from ribosome.machine.state import Info

from myo.logging import Logging
from myo.ui.tmux.server import Server
from myo.ui.tmux.window import Window
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane, PaneAdapter
from myo.command import ShellCommand
from myo.ui.tmux.view_path import ViewPath
from myo.ui.tmux.view import View


def _pos(a):
    return max(a, 0)


def _reverse_weights(weights):
    r = weights / (1 - _)
    norm = sum(r)
    return r / (_ / norm) if norm > 0 else r


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

    is_open = view_open

    def open_views(self, layout):
        return layout.views.filter(self.view_open)

    def open_pane(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        v = path.view
        is_pane = Boolean(isinstance(v, Pane))
        def open(pane):
            def apply(layout):
                set = is_pane.cata(I, lambda a: v.replace_pane(a))
                return (
                    self._split_pane(layout, pane) /
                    set /
                    path.setter.view /
                    Right
                )
            return (self._pane_opener(path, pane).eff(Either) // apply).value
        view = (Task.now(v) if is_pane else
                v.panes.head.task('{} has no panes'.format(v)))
        return view // open

    def _pane_opener(self, path: ViewPath, pane: Pane
                     ) -> Task[Either[str, Layout]]:
        def find_layout():
            return (path.layouts.reversed.find(self.layout_open)
                    .to_either(
                        Fatal('no open layout when trying to open pane')))
        return Task.now(
            self.panes.is_open(pane).no.flat_either_call(
                Left(NothingToDo('{!r} already open'.format(pane))),
                find_layout,
            )
        )

    def _split_pane(self, layout, pane) -> Task[Pane]:
        return self._ref_pane_fatal(layout) / (
            lambda a:
            self.panes.find(a) /
            __.split(layout.horizontal) /
            PaneAdapter /
            pane.open |
            pane
        )

    def _ref_pane_fatal(self, layout) -> Task[Pane]:
        ''' A pane in the layout to be used to open a pane.
        Uses the first open pane available.
        Failure if no panes are open.
        '''
        return (Task.call(self._ref_pane, layout) //
                L(Task.from_maybe)(_, "no ref pane for {}".format(layout)))

    def _ref_pane(self, layout) -> Maybe[Pane]:
        return (
            self._opened_panes(layout.panes).sort_by(_.position | 0).last
            .or_else(layout.layouts.find_map(self._ref_pane))
        )

    def open_pane_path(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        ''' legacy version
        '''
        p = path.view
        return (Task.now(Left('pane {} already open'.format(p)))
                if self.panes.is_open(p)
                else self._open_pane_path(path))

    def _open_in_layouts_path(self, pane, layout, outer):
        if self.layout_open(layout):
            return self._open_in_layout(pane, layout) / (_ + (outer,))
        else:
            return (
                outer.detach_last.map2(F(self._open_in_layouts_path, pane)) |
                Task.failed('cannot open {} without open layout'.format(pane))
            ).map3(lambda p, l, o: (p, layout, o.cat(l)))

    def _open_in_layout(self, pane, layout) -> Task[Tuple[Layout, Pane]]:
        return self._split_pane(layout, pane) & (Task.now(layout))

    def close_pane_path(self, path: ViewPath):
        new_path = path.map_view(__.set(id=Empty()))
        return self.panes.close(path.view) / __.replace(new_path)

    def _opened_panes(self, panes):
        return panes.filter(self.panes.is_open)

    def pack_path(self, path: ViewPath):
        return self.pack_window(path.window) / __.replace(path)

    def pack_window(self, window: Window) -> Task[Either[str, Window]]:
        t = (
            Task.call(window.id.flat_map, self.server.window) //
            L(Task.from_maybe)(_, 'window not found: {}'.format(window)) /
            _.size
        )
        return (
            t.flat_map2(L(self._pack_layout)(window.root, _, _)) /
            Right /
            __.replace(window)
        )

    def _pack_layout(self, l, w, h):
        nop = Task.now(List())
        horizontal = l.horizontal
        total = w if horizontal else h
        @singledispatch
        def recurse(v, size, multi):
            pass
        @recurse.register(Pane)
        def rec_pane(v, size, multi):
            return self._apply_size(v, size, horizontal) if multi else nop
        @recurse.register(Layout)
        def rec_layout(v, size, multi):
            sub_size = (size, h) if horizontal else (w, size)
            return (
                self._pack_layout(v, *sub_size)
                .flat_replace(
                    self._ref_pane_fatal(v) //
                    L(self._apply_size)(_, size, horizontal) if multi else nop
                )
            )
        views = self.open_views(l)
        count = views.length
        if count > 0:
            # each pane spacer takes up one cell
            m = self._measure_layout(views, total - count + 1)
            return (
                self._apply_positions(views, horizontal) +
                views.zip(m).map2(L(recurse)(_, _, count > 1)).sequence(Task)
            )
        else:
            return nop

    def _measure_layout(self, views, total):
        calc = lambda s: s if s > 1 else s * total
        min_s = self.actual_min_sizes(views) / calc
        max_s = self.actual_max_sizes(views) / calc
        weights = self.weights(views)
        return self._balance_sizes(min_s, max_s, weights, total) / round

    def _balance_sizes(self, min_s, max_s, weights, total):
        return self._rectify_sizes(
            self._cut_sizes(min_s, weights, total) if sum(min_s) > total
            else self._distribute_sizes(min_s, max_s, weights, total)
        )

    def _cut_sizes(self, min_s, weights, total):
        self.log.debug('cut sizes: min {}, weights {}, total {}'.format(
            min_s, weights, total))
        surplus = sum(min_s) - total
        dist = _reverse_weights(weights) / (surplus * _)
        cut = (min_s.zip(dist)).map2(sub)
        neg = (cut / (lambda a: a if a < 0 else 0))
        neg_total = sum(neg)
        neg_count = neg.filter(_ < 0).length
        dist2 = neg_total / (min_s.length - neg_count)
        return cut / (lambda a: 0 if a < 0 else a + dist2)

    def _distribute_sizes(self, min_s, max_s, weights, total):
        self.log.debug(
            'distribute sizes: min {}, max {}, weights {}, total {}'.format(
                min_s, max_s, weights, total
            ))
        count = max_s.length
        surplus = total - sum(min_s)
        sizes1 = min_s.zip(max_s, weights).map3(
            lambda l, h, w: min(l + w * surplus, h))
        rest = total - sum(sizes1)
        unsat = (max_s.zip(sizes1)).map2(ne) / Boolean
        unsat_left = count - sum(unsat / _.value) > 0
        def trim_weights():
            w1 = (unsat.zip(weights)).map2(lambda s, w: s.maybe(w))
            return self._normalize_weights(w1)
        def dist_rest():
            rest_w = trim_weights() if unsat_left else weights
            return (sizes1.zip(rest_w)).map2(lambda a, w: a + w * rest)
        return sizes1 if rest <= 0 else dist_rest()

    def _rectify_sizes(self, sizes: List[int]):
        pos = sizes / _pos
        pos_count = sizes.filter(_ >= 2).length
        unders = pos / (lambda a: 2 - a if a < 2 else 0)
        sub = sum(unders) / pos_count
        return pos / (lambda a: 2 if a < 2 else max(2, a - sub))

    def _apply_size(self, pane, size, horizontal):
        self.log.debug('resize {!r} to {} ({})'.format(pane, size, horizontal))
        return (
            self.panes.find_task(pane) //
            __.resize(size, horizontal)
        )

    def _apply_positions(self, views, horizontal):
        if views.length > 1 and views.exists(_.position.is_just):
            quantity = _.left if horizontal else _.top
            ordered = views.sort_by(_.position | 0).reversed
            adapters = self._ref_adapters(ordered)
            current = adapters.sort_by(lambda a: quantity(a) | 0)
            def setpos(current, correct):
                def rec(head, tail):
                    def swap(last, init):
                        if last != head:
                            last.swap(head)
                            return setpos(init.replace_item(head, last), tail)
                        else:
                            return setpos(init, tail)
                    return current.detach_last.map2(swap)
                return correct.detach_head.map2(rec)
            return Task.call(setpos, current, adapters)
        else:
            return Task.now(None)

    def _ref_adapters(self, views):
        return views // self._ref_adapter

    def _ref_adapter(self, view):
        @singledispatch
        def adapter(v):
            pass
        @adapter.register(Pane)
        def pane(v):
            return self.panes.find(v)
        @adapter.register(Layout)
        def layout(v):
            return self._ref_pane(v) // self.panes.find
        return adapter(view)

    def actual_min_sizes(self, views):
        return views / (lambda a: a.effective_fixed_size.or_else(a.min_size) |
                        0)

    def actual_max_sizes(self, views):
        return views / (lambda a: a.effective_fixed_size.or_else(a.max_size) |
                        999)

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

    def find(self, pane: Pane) -> Maybe[PaneAdapter]:
        def find_by_id(pane_id):
            return (
                (pane.session_id & pane.window_id)
                .flat_map2(L(self.select_pane)(_, _, pane_id))
                .or_else(L(self.find_by_id)(pane_id))
            )
        return pane.id // find_by_id

    def find_task(self, pane: Pane) -> Task[PaneAdapter]:
        return (
            Task.call(self.find, pane) //
            L(Task.from_maybe)(_, 'pane not found: {!r}'.format(pane))
        )

    def run_command(self, pane: Pane, command: ShellCommand):
        return self.run_command_line(pane, command.line)

    def run_command_line(self, pane: Pane, line: str):
        return (
            self.find_task(pane) /
            __.run_command(line)
        )

    def command_pid(self, pane: Pane):
        return self.find_task(pane) / _.command_pid

    def close(self, pane: Pane):
        err = 'cannot close pane {}: not found'.format(pane)
        return (Task.call(self.find, pane) //
                __.cata(__.kill.map(Right), lambda: Task.now(Left(err))))

    def close_id(self, id: int):
        return self.server.cmd('kill-pane', '-t', '%{}'.format(id))

    def kill_process(self, pane: Pane, signals):
        return self.find(pane) / L(self._kill_process)(pane, _, signals)

    @task
    def _kill_process(self, pane, adapter, signals):
        def _wait_killed(timeout):
            start = time.time()
            while time.time() - start > timeout and adapter.running:
                time.sleep(.1)
        def kill(signame):
            if adapter.running:
                sig = getattr(signal, 'SIG{}'.format(signame.upper()),
                              signal.SIGINT)
                adapter.command_pid / Process / __.send_signal(sig)
                _wait_killed(3)
            return adapter.not_running
        return (
            signals.find(kill) /
            'process killed by signal {}'.format /
            Info /
            Right |
            Left(Fatal('could not kill running process'))
        )

    def ensure_not_running(self, pane: Pane, kill=False, signals=List('kill')):
        def handle(pa):
            return (
                Task.now(Right(True))
                if pa.not_running else
                self._kill_process(pane, pa, signals=signals)
                if pane.kill or kill else
                Task.now(Left('command already running'))
            )
        return self.find_task(pane) // handle

    def pipe(self, pane: Pane, base: str):
        lg = lambda p: self.log.debug(
            'piping {} to {}'.format(p.name, p.log_path | 'nowhere'))
        return (
            self.find(pane)
            .task(Fatal('pipe: pane not found')) /
            __.pipe(base) /
            pane.setter.log_path %
            lg
        )


class ViewFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.layouts = LayoutFacade(server)
        self.panes = PaneFacade(server)

    def _discern(self, view: View):
        return self.layouts if isinstance(view, Layout) else self.panes

    def is_open(self, view: View):
        return self._discern(view).is_open(view)

__all__ = ('LayoutFacade', 'PaneFacade')
