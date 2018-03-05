from typing import Callable

from amino.state import EitherState
from amino import Maybe, do, Do, List, _, Either, Left, Right
from amino.boolean import false

from myo.config.plugin_state import MyoPluginState
from myo.config.component import MyoComponent

from ribosome.trans.handler import TransHandler, FreeTrans
from ribosome.trans.api import trans


@trans.free.result(trans.st, component=false)
@do(EitherState[MyoPluginState, TransHandler])
def find_handler(pred: Callable[[MyoComponent], Maybe[TransHandler]], desc: str) -> Do:
    components = yield EitherState.inspect(_.components.all)
    eligible: List[FreeTrans] = components.flat_map(_.config).flat_map(pred)
    def select(h: FreeTrans, t: List[FreeTrans]) -> Either[str, TransHandler]:
        return (
            Right(h)
            if t.empty else
            Left(f'multiple handlers for {desc}: {eligible}')
        )
    yield EitherState.lift(eligible.detach_head.map2(select) | Left(f'no handler for {desc}'))


__all__ = ('find_handler',)
