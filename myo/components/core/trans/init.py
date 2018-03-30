from amino import do, Do, _, List
from amino.state import State

from ribosome.trans.api import trans
from ribosome.trans.handler import Trans

from myo.config.handler import find_handlers
from myo.config.plugin_state import MyoPluginState


@trans.free.result(trans.st)
@do(State[MyoPluginState, List[Trans[None]]])
def init_handlers() -> Do:
    yield find_handlers(_.init)


@trans.free.do()
@do(Trans[None])
def init() -> Do:
    handlers = yield find_handlers(_.init)
    yield handlers.sequence(Trans)
    yield Trans.unit


__all__ = ('init',)
