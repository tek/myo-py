from amino import do, Do, __, List
from amino.logging import module_log

from chiasma.util.id import StrIdent, Ident
from chiasma.data.view_tree import ViewTree

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.function import nvim_call_tpe
from ribosome.compute.ribosome_api import Ribo
from ribosome.compute.prog import Prog
from ribosome.compute.program import Program

from myo.ui.data.ui_data import UiData
from myo.ui.data.space import Space
from myo.config.handler import find_handler, find_handler_e
from myo.ui.data.view import Pane, Layout
from myo.ui.data.window import Window
from myo.settings import init_default_ui

log = module_log()


def vim_pid() -> NvimIO[int]:
    return nvim_call_tpe(int, 'getpid')


@do(NS[UiData, None])
def insert_default_ui(ident: Ident, layout_ident: Ident, make_ident: Ident) -> Do:
    pane: ViewTree[Layout, Pane] = ViewTree.pane(Pane.cons(ident=ident, open=True))
    vim_layout = ViewTree.layout(Layout.cons(ident, vertical=True), sub=List(pane))
    make = ViewTree.pane(Pane.cons(ident=make_ident, pin=True))
    make_layout = ViewTree.layout(Layout.cons(make_ident, vertical=True), sub=List(make))
    layout = ViewTree.layout(Layout.cons(layout_ident, vertical=False), sub=List(vim_layout, make_layout))
    yield NS.modify(__.append1.spaces(Space.cons(ident, List(Window.cons(ident, layout=layout)))))


def no_handler(error: str) -> Prog[None]:
    log.error(error)
    return Prog.unit


@prog.do(None)
def init_vim_pane(handler: Program) -> Do:
    pid = yield Ribo.lift_nvimio(vim_pid())
    ident = StrIdent('vim')
    layout_ident = StrIdent('root')
    make_ident = StrIdent('make')
    yield Ribo.lift_comp(insert_default_ui(ident, layout_ident, make_ident), UiData)
    yield handler(ident, pid, True)


@prog.do(None)
def run_init() -> Do:
    handler = yield find_handler_e(__.create_vim_pane(), 'insert_vim_pane')
    yield handler.cata(
        no_handler,
        init_vim_pane,
    )


@prog.do(None)
def init() -> Do:
    allow_init = yield Ribo.setting_prog(init_default_ui)
    yield run_init() if allow_init else Prog.unit


__all__ = ('init',)
