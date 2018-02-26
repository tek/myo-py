from amino import do, Do, Maybe, __, _, L
from amino.state import EitherState
from amino.dat import Dat
from amino.boolean import false

from ribosome.trans.api import trans, transm_lift_s
from ribosome.trans.handler import TransHandler, FreeTrans
from ribosome.plugin_state import PluginState
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.config.component import MyoComponent
from myo.env import Env
from myo.settings import MyoSettings
from myo.config.handler import find_handler
from myo.data.command import Command
from myo.components.ui.trans.pane import ui_pane_by_ident
from myo.components.command.trans.history import push_history


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
def run_command_with_target(handler: FreeTrans, cmd: Command, target: Ident) -> None:
    pane = yield ui_pane_by_ident(target).switch
    yield handler(cmd, pane).switch


@trans.free.do()
@do(TransM)
def run_command_without_target(handler: FreeTrans, cmd: Command) -> None:
    yield handler(cmd).switch


@trans.free.do()
@do(TransM)
def run_command(ident: Ident, options: RunCommandOptions) -> Do:
    cmd = yield transm_lift_s(EitherState.inspect_f(__.comp.command_by_ident(ident)))
    target = cmd.interpreter.target
    handler = yield run_handler(cmd).m
    yield (target / L(run_command_with_target)(handler, cmd, _) | (lambda: run_command_without_target(handler, cmd))).m
    yield push_history(cmd, target).m


__all__ = ('run_command',)
