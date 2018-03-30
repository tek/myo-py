from amino import do, Do, __, List, _
from amino.lenses.lens import lens

from chiasma.util.id import StrIdent, Ident
from chiasma.data.view_tree import ViewTree

from ribosome.trans.api import trans
from ribosome.nvim.io.state import NS
from ribosome.nvim.io.compute import NvimIO
from ribosome.trans.action import Trans
from ribosome.nvim.api.function import nvim_call_tpe

from myo.ui.data.ui_data import UiData
from myo.ui.data.space import Space
from myo.config.handler import find_handler
from myo.ui.data.view import Pane, Layout
from myo.ui.data.window import Window
from myo.settings import setting_trans


def vim_pid() -> NvimIO[int]:
    return nvim_call_tpe(int, 'getpid')


@do(NS[UiData, None])
def insert_default_ui(ident: Ident, layout_ident: Ident, make_ident: Ident) -> Do:
    pane: ViewTree[Layout, Pane] = ViewTree.pane(Pane.cons(ident=ident, open=True))
    vim_layout = ViewTree.layout(Layout.cons(ident, vertical=True), sub=List(pane))
    make = ViewTree.pane(Pane.cons(ident=make_ident))
    make_layout = ViewTree.layout(Layout.cons(make_ident, vertical=True), sub=List(make))
    layout = ViewTree.layout(Layout.cons(layout_ident, vertical=False), sub=List(vim_layout, make_layout))
    yield NS.modify(__.append1.spaces(Space.cons(ident, List(Window.cons(ident, layout=layout)))))


@trans.free.do()
@do(Trans)
def init() -> Do:
    allow_init = yield setting_trans(_.init_default_ui)
    if allow_init:
        handler = yield find_handler(__.create_vim_pane(), 'insert_vim_pane')
        pid = yield NS.lift(vim_pid()).trans
        ident = StrIdent('vim')
        layout_ident = StrIdent('root')
        make_ident = StrIdent('make')
        yield insert_default_ui(ident, layout_ident, make_ident).zoom(lens.comp).trans
        yield handler(ident, pid)


__all__ = ('init',)
