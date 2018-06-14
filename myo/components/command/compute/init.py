from amino import do, Do

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.compute.tpe import CommandRibosome
from myo.components.command.compute.history import restore_history
from myo.settings import load_history


@prog
@do(NS[CommandRibosome, None])
def command_init() -> Do:
    want_load_history = yield Ribo.setting(load_history)
    if want_load_history:
        yield Ribo.zoom_comp(restore_history())


__all__ = ('command_init',)
