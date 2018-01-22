from numbers import Number
from typing import Callable
from operator import ne, sub

from amino.dispatch import PatMat
from amino import Either, Dat, _, List, Boolean, Maybe, Nil

from ribosome import ribo_log

from myo.ui.data.tree import ViewTree, PaneNode, LayoutNode
from myo.ui.data.view import Layout, Pane, View
from myo.ui.data.window import Window


class Measures(Dat['Measures']):

    def __init__(self, size: int) -> None:
        self.size = size


class MeasuredLayout(Dat['MeasuredLayout']):

    def __init__(self, layout: Layout, measures: Measures) -> None:
        self.layout = layout
        self.measures = measures


class MeasuredPane(Dat['MeasuredPane']):

    def __init__(self, pane: Pane, measures: Measures) -> None:
        self.pane = pane
        self.measures = measures


MeasureTree = ViewTree[MeasuredLayout, MeasuredPane]
MeasuredLayoutNode = LayoutNode[MeasuredLayout, MeasuredPane]
MeasuredPaneNode = PaneNode[MeasuredLayout, MeasuredPane]


class is_view_open(PatMat, alg=ViewTree):

    def pane_node(self, node: PaneNode[Layout, Pane]) -> Either[str, Pane]:
        return node.data.open

    def layout_node(self, node: LayoutNode[Layout, Pane]) -> Either[str, Pane]:
        return node.sub.exists(self)


def open_views(node: LayoutNode[Layout, Pane]) -> List[View]:
    return node.sub.filter(is_view_open.match)


def measure_layout_views(views: List[View], total: int) -> List[int]:
    # each pane spacer takes up one cell
    pane_spacers = views.length - 1
    cells = total - pane_spacers
    in_cells = lambda s: s if s > 1 else s * cells
    min_s = actual_min_sizes(views) / in_cells
    max_s = actual_max_sizes(views) / in_cells
    return balance_sizes(min_s, max_s, weights(views), cells) / round


class measure_layout(PatMat, alg=ViewTree):

    def __init__(self, measures: Measures, width: int, height: int) -> None:
        self.measures = measures
        self.width = width
        self.height = height

    def pane_node(self, node: PaneNode[Layout, Pane]) -> MeasureTree:
        return ViewTree.pane(MeasuredPane(node.data, self.measures))

    def layout_node(self, node: LayoutNode[Layout, Pane]) -> MeasureTree:
        vertical = node.data.vertical
        total = self.height if vertical else self.width
        views = open_views(node)
        def recurse(next_node: ViewTree[Layout, Pane], size: int) -> MeasureTree:
            new_width, new_height = (self.width, size) if vertical else (size, self.height)
            next_measures = Measures(size)
            return measure_layout(next_measures, new_width, new_height)(next_node)
        def measure_views() -> List[MeasureTree]:
            sizes = measure_layout_views(views / _.data, total)
            return views.zip(sizes).map2(recurse)
        sub = (
            measure_views()
            if views.length > 0 else
            Nil
        )
        return ViewTree.layout(MeasuredLayout(node.data, self.measures), sub)


def measure_window(window: Window, width: int, height: int) -> MeasureTree:
    size = height if window.layout.data.vertical else width
    return measure_layout(Measures(size), width, height)(window.layout)


def _pos(a: int) -> int:
    return max(a, 0)


def _reverse_weights(weights):
    r = weights / (1 - _)
    norm = sum(r)
    return r / (_ / norm) if norm > 0 else r


def actual_sizes(views: List[View], attr: Callable[[View], Maybe[Number]], default: int) -> List[Number]:
    return views / (lambda a: a.effective_fixed_size.or_else(attr(a.geometry)) | default)


def actual_min_sizes(views: List[View]) -> List[Number]:
    return actual_sizes(views, _.min_size, 0)


def actual_max_sizes(views: List[View]) -> List[Number]:
    return actual_sizes(views, _.max_size, 999)


def normalize_weights(weights: List[float]) -> List[float]:
    amended = amend_weights(weights)
    total = sum(amended)
    total1 = 1 if total == 0 else total
    return amended / (_ / total1)


def weights(views: List[View]) -> List[float]:
    return normalize_weights(views / _.effective_weight)


def balance_sizes(min_s: int, max_s: int, weights: List[float], total: int):
    fitted = (
        cut_sizes(min_s, weights, total)
        if sum(min_s) > total else
        distribute_sizes(min_s, max_s, weights, total)
    )
    return rectify_sizes(fitted)


def rectify_sizes(sizes: List[int]) -> List[int]:
    pos = sizes / _pos
    pos_count = sizes.filter(_ >= 2).length
    unders = pos / (lambda a: 2 - a if a < 2 else 0)
    sub = sum(unders) / pos_count
    return pos / (lambda a: 2 if a < 2 else max(2, a - sub))


def cut_sizes(min_s: int, weights: List[float], total: int) -> List[int]:
    ribo_log.debug(f'cut sizes: min {min_s}, weights {weights}, total {total}')
    surplus = sum(min_s) - total
    dist = _reverse_weights(weights) / (surplus * _)
    cut = (min_s.zip(dist)).map2(sub)
    neg = (cut / (lambda a: a if a < 0 else 0))
    neg_total = sum(neg)
    neg_count = neg.filter(_ < 0).length
    dist2 = neg_total / (min_s.length - neg_count)
    return cut / (lambda a: 0 if a < 0 else a + dist2)


def distribute_sizes(min_s: int, max_s: int, weights: List[float], total: int) -> List[int]:
    ribo_log.debug(f'distribute sizes: min {min_s}, max {max_s}, weights {weights}, total {total}')
    count = max_s.length
    surplus = total - sum(min_s)
    sizes1 = min_s.zip(max_s, weights).map3(
        lambda l, h, w: min(l + w * surplus, h))
    rest = total - sum(sizes1)
    unsat = (max_s.zip(sizes1)).map2(ne) / Boolean
    unsat_left = count - sum(unsat / _.value) > 0
    def trim_weights():
        w1 = (unsat.zip(weights)).map2(lambda s, w: s.maybe(w))
        return normalize_weights(w1)
    def dist_rest():
        rest_w = trim_weights() if unsat_left else weights
        return (sizes1.zip(rest_w)).map2(lambda a, w: a + w * rest)
    return sizes1 if rest <= 0 else dist_rest()


def amend_weights(weights: List[float]) -> List[float]:
    total = sum(weights.join)
    total1 = 1 if total == 0 else total
    empties = weights.filter(_.is_empty).length
    empties1 = 1 if empties == 0 else empties
    empty = total1 / empties1
    return weights / (_ | empty)


__all__ = ('measure_layout', 'measure_window')
