from amino import do, Do, __, List
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


def vim_pid() -> NvimIO[int]:
    return nvim_call_tpe(int, 'getpid')


@do(NS[UiData, None])
def insert_vim_ui(ident: Ident, layout_ident: Ident) -> Do:
    pane = ViewTree.pane(Pane.cons(ident=ident, open=True))
    inner = ViewTree.layout(Layout.cons(ident, vertical=True), sub=List(pane))
    layout = ViewTree.layout(Layout.cons(layout_ident, vertical=False), sub=List(inner))
    yield NS.modify(__.append1.spaces(Space.cons(ident, List(Window.cons(ident, layout=layout)))))


@trans.free.do()
@do(Trans)
def stage1() -> Do:
    handler = yield find_handler(__.create_vim_pane(), 'insert_vim_pane').m
    ident = StrIdent('vim')
    layout_ident = StrIdent('root')
    yield insert_vim_ui(ident, layout_ident).zoom(lens.comp).trans
    pid = yield NS.lift(vim_pid()).trans
    yield handler(ident, pid).m
    yield NS.unit

__all__ = ('stage1',)
