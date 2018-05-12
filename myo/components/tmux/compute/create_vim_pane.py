from amino import do, Do, Either, Just
from amino.logging import module_log

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.io.state import TS
from chiasma.data.tmux import TmuxData
from chiasma.util.id import Ident
from chiasma.commands.pane import pane
from chiasma.data.pane import Pane
from chiasma.data.session import Session
from chiasma.data.window import Window
from chiasma.util.pid import discover_pane_by_pid

from myo.components.tmux.tpe import TmuxRibosome
from myo.settings import vim_tmux_pane

log = module_log()


@do(TS[TmuxData, None])
def insert_vim_pane(
        ident: Ident,
        override_id: Either[str, int],
        vim_pid: int,
) -> Do:
    pane_data = yield TS.lift(override_id.cata(lambda err: discover_pane_by_pid(vim_pid), pane))
    vim_pane = Pane.cons(ident, id=pane_data.id)
    yield TS.modify(
        lambda s:
        s
        .append1.panes(vim_pane)
        .append1.windows(Window.cons(ident, id=pane_data.window_id))
        .append1.sessions(Session.cons(ident, id=pane_data.session_id))
        .set.vim_pane(Just(vim_pane.ident))
    )


@prog
@do(NS[TmuxRibosome, None])
def create_vim_pane(ident: Ident, vim_pid: int) -> Do:
    override = yield Ribo.setting_e(vim_tmux_pane)
    yield Ribo.zoom_comp(insert_vim_pane(ident, override, vim_pid).nvim)


__all__ = ('create_vim_pane',)