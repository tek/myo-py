from amino import do, Do
from amino.state import State

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData

from myo.components.core.data import CoreData
from myo.env import Env


@trans.free.unit(trans.st)
@do(State[ComponentData[Env, CoreData], None])
def stage1() -> Do:
    yield State.pure(None)


__all__ = ('stage1',)
