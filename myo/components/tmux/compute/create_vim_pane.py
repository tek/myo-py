from amino import do, Do, Either, Just, env
from amino.logging import module_log
from amino.lenses.lens import lens

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.io.state import TS
from myo.components.tmux.data import TmuxData
from chiasma.util.id import Ident
from chiasma.commands.pane import pane, parse_pane_id
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
        pane_id: Either[str, int],
        vim_pid: int,
) -> Do:
    pane_data = yield TS.lift(pane_id.cata(lambda err: discover_pane_by_pid(vim_pid), pane))
    vim_pane = Pane.cons(ident, id=pane_data.id)
    yield TS.modify(
        lambda s:
        s
        .append1.panes(vim_pane)
        .append1.windows(Window.cons(ident, id=pane_data.window_id))
        .append1.sessions(Session.cons(ident, id=pane_data.session_id))
    ).zoom(lens.views)
    yield TS.modify(lambda s: s.set.vim_pane(Just(vim_pane.ident)))


@prog
@do(NS[TmuxRibosome, None])
def create_vim_pane(ident: Ident, vim_pid: int, use_env_pane: bool) -> Do:
    env_pane = env.get('TMUX_PANE').flat_map(parse_pane_id)
    override = yield Ribo.setting_e(vim_tmux_pane)
    strict = override.o(env_pane) if use_env_pane else override
    yield Ribo.zoom_comp(insert_vim_pane(ident, strict, vim_pid).nvim)


__all__ = ('create_vim_pane',)
