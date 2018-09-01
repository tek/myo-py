from amino import do, Do

from ribosome.compute.api import prog

from chiasma.util.id import IdentSpec
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.compute.tpe import CommandRibosome
from myo.util.id import ensure_ident_ns
from myo.components.command.data import running_command
from myo.util.process import kill_process


@prog
@do(NS[CommandRibosome, None])
def kill(ident_spec: IdentSpec) -> Do:
    ident = yield ensure_ident_ns(ident_spec)
    cmd_e = yield Ribo.zoom_comp(running_command(ident))
    cmd = yield NS.e(cmd_e)
    pid = yield NS.m(cmd.pid, lambda: f'cannot kill command `{ident}`: no associated pid')
    yield NS.from_io(kill_process(pid))


__all__ = ('kill',)
