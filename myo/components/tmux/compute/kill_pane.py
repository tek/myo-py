from amino import do, Do
from amino.lenses.lens import lens

from ribosome.compute.api import prog

from chiasma.util.id import Ident
from chiasma.pane import pane_by_ident
from chiasma.io.state import TS
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from myo.components.tmux.tpe import TmuxRibosome
from myo.tmux.pid import process_pid
from myo.util.process import kill_process
from myo.components.tmux.pane import pane_id_by_ident


@prog
@do(NS[TmuxRibosome, None])
def tmux_kill_pane(ident: Ident) -> Do:
    pane_id = yield pane_id_by_ident(ident)
    pane = yield Ribo.zoom_comp(pane_by_ident(ident).nvim.zoom(lens.views))
    pane_id = yield NS.m(pane.id, lambda: f'pane `{ident}` has no id')
    pid_m = yield TS.lift(process_pid(pane_id)).nvim
    pid = yield NS.m(pid_m, lambda: f'pane `{ident}` has no running process')
    # signal!
    yield NS.from_io(kill_process(pid))
    yield NS.unit


__all__ = ('tmux_kill_pane',)
