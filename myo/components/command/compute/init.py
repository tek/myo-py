from amino import do, Do

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.compute.tpe import CommandRibosome
from myo.components.command.compute.history import load_history


@prog
@do(NS[CommandRibosome, None])
def command_init() -> Do:
    yield Ribo.zoom_comp(load_history())


__all__ = ('command_init',)
