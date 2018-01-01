from ribosome.trans.api import trans
from ribosome.plugin_state import PluginState

from amino import do, Do, Boolean
from amino.state import EitherState
from amino.boolean import true

from myo.util import Ident
from myo import MyoSettings, Env, MyoComponent
from myo.data.command import Command


@trans.free.unit(trans.st)
@do(EitherState[PluginState[MyoSettings, Env, MyoComponent], None])
def run_command(name: Ident) -> Do:
    yield EitherState.pure(None)


def tmux_can_run(cmd: Command) -> Boolean:
    return true


__all__ = ('run_command', 'tmux_can_run')
