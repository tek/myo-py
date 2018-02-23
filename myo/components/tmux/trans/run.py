from ribosome.trans.api import trans
from ribosome.plugin_state import PluginState

from chiasma.io.state import TS

from amino import do, Do, Boolean
from amino.boolean import true

from myo.util import Ident
from myo.data.command import Command
import myo.tmux.trans  # noqa
from myo.settings import MyoSettings
from myo.env import Env
from myo.config.component import MyoComponent


@trans.free.unit(trans.st)
@do(TS[PluginState[MyoSettings, Env, MyoComponent], None])
def run_command(name: Ident) -> Do:
    yield TS.pure(None)


def tmux_can_run(cmd: Command) -> Boolean:
    return true


__all__ = ('run_command', 'tmux_can_run')
