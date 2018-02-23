from amino import do, Do
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData

from chiasma.render import render
from chiasma.data.tmux import TmuxData
from chiasma.io.state import TS
from chiasma.util.id import Ident
from chiasma.data.view_tree import ViewTree

from myo.ui.data.view import Pane, Layout
from myo.env import Env


@trans.free.result(trans.st)
@do(TS[ComponentData[Env, TmuxData], None])
def tmux_render(session: Ident, window: Ident, layout: ViewTree[Pane, Layout]) -> Do:
    yield render(P=Pane, L=Layout)(session, window, layout).transform_s_lens(lens.comp)


__all__ = ('tmux_render',)
