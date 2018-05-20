from myo.components.tmux.data import TmuxData
from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import close_pane_id
from chiasma.io.state import TS

from amino import do, Do, _

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.config.component import ComponentData

from myo.env import Env


@prog
@do(NS[ComponentData[Env, TmuxData], None])
def tmux_quit() -> Do:
    all_panes = yield NS.inspect(_.comp.views.panes)
    vim_pane_ident = yield NS.inspect(_.comp.vim_pane)
    close_panes = all_panes.filter(lambda a: not vim_pane_ident.contains(a.ident))
    yield TS.lift(close_panes.flat_map(_.id).traverse(close_pane_id, TmuxIO)).nvim


__all__ = ('tmux_quit',)
