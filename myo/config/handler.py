from typing import Callable

from amino import Maybe, do, Do, List, _, Either, Left, Right
from amino.logging import module_log

from myo.config.plugin_state import MyoState
from myo.config.component import MyoComponent

from ribosome.compute.program import Program
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.nvim.io.api import N
from ribosome.compute.prog import Prog

log = module_log()


@prog
@do(NS[MyoState, List[Program]])
def find_handlers(pred: Callable[[MyoComponent], Maybe[Program]]) -> Do:
    components = yield NS.inspect(_.components.all)
    return components.flat_map(_.config).flat_map(pred)


@prog
@do(NS[MyoState, Either[str, Program]])
def select_handler(eligible: List[Program], desc: str) -> Do:
    def select(h: Program, t: List[Program]) -> Either[str, Program]:
        return (
            Right(h)
            if t.empty else
            Left(f'multiple handlers for `{desc}`: {eligible}')
        )
    yield NS.pure(eligible.detach_head.to_either(f'no handler for `{desc}`').flat_map2(select))


@prog.do(Either[str, Program])
def find_handler_e(pred: Callable[[MyoComponent], Maybe[Program]], desc: str) -> Do:
    eligible = yield find_handlers(pred)
    yield select_handler(eligible, desc)


@prog.do(Program)
def find_handler(pred: Callable[[MyoComponent], Maybe[Program]], desc: str) -> Do:
    handler_e = yield find_handler_e(pred, desc)
    yield Prog.e(handler_e)


__all__ = ('find_handler', 'find_handlers', 'find_handler_e',)
