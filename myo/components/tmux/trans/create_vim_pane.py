from amino import do, Do, _, Either, Just
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.nvim.io import NS
from ribosome.dispatch.component import ComponentData
from ribosome.config.config import Resources

from chiasma.io.state import TS
from chiasma.data.tmux import TmuxData
from chiasma.util.id import Ident
from chiasma.commands.pane import all_panes, pane
from chiasma.io.compute import TmuxIO
from chiasma.data.pane import Pane
from chiasma.data.session import Session
from chiasma.data.window import Window

from myo.env import Env
from myo.config.component import MyoComponent
from myo.settings import MyoSettings


@do(TmuxIO)
def discover_pane(vim_pid: int) -> Do:
    panes = yield all_panes()
    yield TmuxIO.from_maybe(panes.find(_.pid == vim_pid), f'could not find vim pane with pid `{vim_pid}`')


@do(TS[TmuxData, None])
def insert_vim_pane(
        ident: Ident,
        override_id: Either[str, int],
        vim_pid: int,
) -> Do:
    pane_data = yield TS.lift(override_id.cata(lambda err: discover_pane(vim_pid), pane))
    yield TS.modify(
        lambda s:
        s
        .append1.panes(Pane.cons(ident, id=pane_data.id))
        .append1.windows(Window.cons(ident, id=pane_data.window_id))
        .append1.sessions(Session.cons(ident, id=pane_data.session_id))
    )


@trans.free.result(trans.st)
@do(NS[Resources[ComponentData[Env, TmuxData], MyoSettings, MyoComponent], None])
def create_vim_pane(ident: Ident, vim_pid: int) -> Do:
    override = yield NS.inspect_f(_.settings.vim_tmux_pane.value)
    yield insert_vim_pane(ident, override, vim_pid).zoom(lens.data.comp).nvim


__all__ = ('create_vim_pane',)
