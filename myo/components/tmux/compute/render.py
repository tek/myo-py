from amino import do, Do
from amino.lenses.lens import lens

from ribosome.compute.api import prog
from ribosome.config.component import ComponentData
from ribosome.nvim.io.state import NS

from chiasma.render import render
from myo.components.tmux.data import TmuxData
from chiasma.util.id import Ident
from chiasma.data.view_tree import ViewTree

from myo.ui.data.view import Pane, Layout
from myo.env import Env


@prog
@do(NS[ComponentData[Env, TmuxData], None])
def tmux_render(session: Ident, window: Ident, layout: ViewTree[Pane, Layout]) -> Do:
    yield render(P=Pane, L=Layout)(session, window, layout).zoom(lens.comp.views).nvim


__all__ = ('tmux_render',)
