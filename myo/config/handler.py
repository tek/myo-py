from typing import Callable

from amino.state import EitherState
from amino import Maybe, do, Do, List, _, Either, Left, Right
from amino.boolean import false

from myo.config.plugin_state import MyoPluginState
from myo.config.component import MyoComponent

from ribosome.trans.handler import Trans
from ribosome.trans.api import trans


@trans.free.result(trans.st, component=false)
@do(EitherState[MyoPluginState, List[Trans]])
def find_handlers(pred: Callable[[MyoComponent], Maybe[Trans]]) -> Do:
    components = yield EitherState.inspect(_.components.all)
    return components.flat_map(_.config).flat_map(pred)


@trans.free.result(trans.st, component=false)
@do(EitherState[MyoPluginState, Trans])
def find_handler(pred: Callable[[MyoComponent], Maybe[Trans]], desc: str) -> Do:
    eligible = yield find_handlers.fun(pred)
    def select(h: Trans, t: List[Trans]) -> Either[str, Trans]:
        return (
            Right(h)
            if t.empty else
            Left(f'multiple handlers for {desc}: {eligible}')
        )
    yield EitherState.lift(eligible.detach_head.map2(select) | Left(f'no handler for {desc}'))


__all__ = ('find_handler', 'find_handlers')
