from typing import Callable

from amino import Maybe, do, Do, List, _, Either, Left, Right

from myo.config.plugin_state import MyoPluginState
from myo.config.component import MyoComponent

from ribosome.compute.prog import Program, Prog
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.nvim.io.api import N


@prog
@do(NS[MyoPluginState, List[Program]])
def find_handlers(pred: Callable[[MyoComponent], Maybe[Program]]) -> Do:
    components = yield NS.inspect(_.components.all)
    return components.flat_map(_.config).flat_map(pred)


@prog
@do(NS[MyoPluginState, Program])
def select_handler(eligible: List[Program], desc: str) -> Do:
    def select(h: Program, t: List[Program]) -> Either[str, Program]:
        return (
            Right(h)
            if t.empty else
            Left(f'multiple handlers for {desc}: {eligible}')
        )
    yield NS.lift(eligible.detach_head.map2(select) | N.error(f'no handler for {desc}'))


@prog.do
@do(Prog[Program])
def find_handler(pred: Callable[[MyoComponent], Maybe[Program]], desc: str) -> Do:
    eligible = yield find_handlers(pred)
    yield select_handler(eligible, desc)


__all__ = ('find_handler', 'find_handlers')
