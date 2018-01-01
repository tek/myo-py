from amino import do, Do, Maybe, __, Either, List, Left, _
from amino.state import EitherState
from amino.dat import Dat
from amino.boolean import false

from ribosome.trans.api import trans
from ribosome.trans.handler import TransHandler
from ribosome.plugin_state import PluginState
from ribosome.trans.action import TransM

from myo import Env, MyoSettings
from myo.util import Ident
from myo.config.component import MyoComponent


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
    eligible = yield EitherState.inspect(__.components.all.filter(__.config.exists(__.can_run(cmd))))
    def select(h: MyoComponent, t: List[MyoComponent]) -> Either[str, TransHandler]:
        return (
            h.config.flat_map(_.run).to_either(f'{h} has no runner')
            if t.empty else
            Left(f'multiple handlers for {cmd}: {eligible}')
        )
    yield EitherState.lift(eligible.detach_head.map2(select) | Left(f'no handler for {cmd}'))


@trans.free.do()
@do(TransM)
def run_command(name: Ident, options: RunCommandOptions) -> Do:
    handler = yield run_handler(name).m
    yield handler(name).m


__all__ = ('run_command',)
