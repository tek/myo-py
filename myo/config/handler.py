from typing import Callable

from amino.state import EitherState
from amino import Maybe, do, Do, List, _, __, Either, Left

from myo.config.plugin_state import MyoPluginState
from myo.config.component import MyoComponent, Comp

from ribosome.trans.handler import TransHandler


@do(EitherState[MyoPluginState, TransHandler])
def find_handler(
        pred: Callable[[MyoComponent], bool],
        trans: Callable[[MyoComponent], Maybe[TransHandler]],
        desc: str
) -> Do:
    components = yield EitherState.inspect(_.components.all)
    eligible: List[Comp] = components.filter(__.config.exists(pred))
    def select(h: Comp, t: List[Comp]) -> Either[str, TransHandler]:
        return (
            h.config.flat_map(trans).to_either(f'{h} has no runner')
            if t.empty else
            Left(f'multiple handlers for {desc}: {eligible}')
        )
    yield EitherState.lift(eligible.detach_head.map2(select) | Left(f'no handler for {desc}'))


__all__ = ('find_handler',)
