# from __future__ import annotations
from typing import Tuple

from amino import do, Do, Dat, Maybe, Just, Nothing

from chiasma.util.id import IdentSpec
from chiasma.open_pane import ui_open_pane
from chiasma.data.view_tree import ViewTree
from amino.logging import module_log
from amino.case import Case

from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.io.state import NS
from ribosome.compute.prog import Prog

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.pane import map_window_trees, find_in_ui
from myo.components.ui.compute.pane import render_view
from myo.ui.data.view_tree import MyoViewTree, MyoPaneNode
from myo.ui.data.view import Pane
from myo.util.id import ensure_ident_prog
from myo.ui.data.window import Window
from myo.components.ui.compute.handler import ui_handler

log = module_log()


class OpenPaneOptions(Dat['OpenPaneOptions']):

    def __init__(self) -> None:
        pass


class match_pane_ident(Case[MyoViewTree, Maybe[Pane]], alg=ViewTree):

    def __init__(self, ident: Ident) -> None:
        self.ident = ident

    def pane(self, pane: MyoPaneNode) -> Maybe[Pane]:
        return Just(pane.data) if pane.data.ident == self.ident else Nothing

    def case_default(self, node: MyoViewTree) -> Maybe[Pane]:
        return Nothing


@do(NS[UiData, Tuple[bool, Window, Pane]])
def chiasma_open_pane(ident: Ident) -> Do:
    pane_m = yield find_in_ui(match_pane_ident(ident))
    (space, window, pane) = yield NS.m(pane_m, lambda: f'no pane named `{ident}`')
    if not pane.open:
        yield map_window_trees(lambda a: ui_open_pane(ident)(a).get_or_strict(a)).nvim
    return (not pane.open), window, pane


@prog.do(bool)
def pane_was_closed(ident: Ident, window: Window, pane: Pane) -> Do:
    pane_open = yield ui_handler(ident, lambda a: a.window_pane_open, 'window_pane_open')
    open = yield pane_open(window, pane)
    return not open


@prog.do(None)
def open_pane(ident_spec: IdentSpec, options: OpenPaneOptions) -> Do:
    ident = yield ensure_ident_prog(ident_spec)
    was_closed, window, pane = yield Ribo.lift_comp(chiasma_open_pane(ident), UiData)
    inconsistent = yield Prog.pure(True) if was_closed else pane_was_closed(ident, window, pane)
    if inconsistent:
        yield render_view(ident)


__all__ = ('open_pane',)
