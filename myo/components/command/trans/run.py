from amino import do, Do, Maybe, __, _
from amino.state import EitherState
from amino.dat import Dat
from amino.boolean import false

from ribosome.trans.api import trans, transm_lift_s
from ribosome.trans.handler import TransHandler
from ribosome.plugin_state import PluginState
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.config.component import MyoComponent
from myo.env import Env
from myo.settings import MyoSettings
from myo.config.handler import find_handler
from myo.data.command import Command
from myo.components.ui.trans.pane import ui_pane_by_ident


class RunCommandOptions(Dat['RunCommandOptions']):

    def __init__(
            self,
            interpreter: Maybe[str],
    ) -> None:
        self.interpreter = interpreter


@trans.free.result(trans.st, component=false)
@do(EitherState[PluginState[MyoSettings, Env, MyoComponent], TransHandler])
def run_handler(cmd: Command) -> Do:
    yield find_handler(__.can_run(cmd), _.run, str(cmd))


@trans.free.do()
@do(TransM)
def run_command(ident: Ident, options: RunCommandOptions) -> Do:
    cmd = yield transm_lift_s(EitherState.inspect_f(__.command_by_ident(ident)), component=false)
    handler = yield run_handler(cmd).m
    pane = yield ui_pane_by_ident(cmd.interpreter.target).switch
    yield handler(cmd, pane).switch


__all__ = ('run_command',)
