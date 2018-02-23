from amino import do, Do, Maybe, __, _
from amino.state import EitherState
from amino.dat import Dat
from amino.boolean import false

from ribosome.trans.api import trans
from ribosome.trans.handler import TransHandler
from ribosome.plugin_state import PluginState
from ribosome.trans.action import TransM

from myo import Env, MyoSettings
from myo.util import Ident
from myo.config.component import MyoComponent, find_handler


class RunCommandOptions(Dat['RunCommandOptions']):

    def __init__(
            self,
            interpreter: Maybe[str],
    ) -> None:
        self.interpreter = interpreter


@trans.free.result(trans.st, component=false)
@do(EitherState[PluginState[MyoSettings, Env, MyoComponent], TransHandler])
def run_handler(ident: Ident) -> Do:
    cmd = yield EitherState.inspect_f(__.data.command_by_ident(ident))
    yield find_handler(__.can_run(cmd), _.run, str(cmd))


@trans.free.do()
@do(TransM)
def run_command(name: Ident, options: RunCommandOptions) -> Do:
    handler = yield run_handler(name).m
    yield handler(name).m


__all__ = ('run_command',)
