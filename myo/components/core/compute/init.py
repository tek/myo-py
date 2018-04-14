from amino import do, Do, _, List
from amino.state import State

from ribosome.compute.api import prog
from ribosome.compute.prog import Program, Prog, bind_nullary_program

from myo.config.handler import find_handlers
from myo.config.plugin_state import MyoPluginState


@prog
@do(State[MyoPluginState, List[Program[None]]])
def init_handlers() -> Do:
    yield find_handlers(_.init)


@prog.do
@do(Prog[None])
def init() -> Do:
    handlers = yield find_handlers(_.init)
    yield handlers.traverse(bind_nullary_program, Prog)
    yield Prog.unit


__all__ = ('init',)
