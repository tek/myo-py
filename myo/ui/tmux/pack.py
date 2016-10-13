from functools import singledispatch  # type: ignore
from operator import ne, sub

from amino import Either, Task, L, _, Right, __, List, Boolean, Just, Empty

from myo.logging import Logging
from myo.ui.tmux.window import Window
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.facade.window import WindowFacade
from myo.ui.tmux.view import View


class WindowPacker(Logging):

    def __init__(self, window: WindowFacade) -> None:
        self.window = window

    @property
    def run(self) -> Task[Either[str, Window]]:
        w, h = self.window.window_size
        return (
            self._pack_layout(self.window.root, w, h) /
            Right /
            __.replace(self.window)
        )

    def _loc(self, pane: Pane):
        return self.window.loc(pane)

    def _pack_layout(self, l, w, h):
        nop = Task.now(Empty())
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
                    self.window.ref_pane_fatal(v) //
                    L(self._apply_size)(_, size, horizontal) if multi else nop
                )
            )
        views = self.window.open_views(l)
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
        min_s = _actual_min_sizes(views) / calc
        max_s = _actual_max_sizes(views) / calc
        weights = _weights(views)
        return self._balance_sizes(min_s, max_s, weights, total) / round

    def _balance_sizes(self, min_s, max_s, weights, total):
        return _rectify_sizes(
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
            return _normalize_weights(w1)
        def dist_rest():
            rest_w = trim_weights() if unsat_left else weights
            return (sizes1.zip(rest_w)).map2(lambda a, w: a + w * rest)
        return sizes1 if rest <= 0 else dist_rest()

    def _apply_size(self, pane, size, horizontal):
        self.log.debug('resize {} to {} ({})'.format(pane, size,
                                                     bool(horizontal)))
        return (
            self.window.native_pane_task_fatal(pane) //
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
            return Task.now(Empty())

    def _ref_adapters(self, views):
        return views // self._ref_adapter

    def _ref_adapter(self, view: View):
        ref = Just(view) if isinstance(view, Pane) else self._ref_pane(view)
        return ref // self.window.native_pane


def _pos(a):
    return max(a, 0)


def _reverse_weights(weights):
    r = weights / (1 - _)
    norm = sum(r)
    return r / (_ / norm) if norm > 0 else r


def _rectify_sizes(sizes: List[int]):
    pos = sizes / _pos
    pos_count = sizes.filter(_ >= 2).length
    unders = pos / (lambda a: 2 - a if a < 2 else 0)
    sub = sum(unders) / pos_count
    return pos / (lambda a: 2 if a < 2 else max(2, a - sub))


def _actual_min_sizes(views):
    return views / (lambda a: a.effective_fixed_size.or_else(a.min_size) |
                    0)


def _actual_max_sizes(views):
    return views / (lambda a: a.effective_fixed_size.or_else(a.max_size) |
                    999)


def _weights(views):
    return _normalize_weights(views / _.effective_weight)


def _normalize_weights(weights):
    amended = amend_weights(weights)
    total = sum(amended)
    total1 = 1 if total == 0 else total
    return amended / (_ / total1)


def amend_weights(weights):
    total = sum(weights.join)
    total1 = 1 if total == 0 else total
    empties = weights.filter(_.is_empty).length
    empties1 = 1 if empties == 0 else empties
    empty = total1 / empties1
    return weights / (_ | empty)

__all__ = ('WindowPacker',)
