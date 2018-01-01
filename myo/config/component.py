from typing import Callable

from amino import Dat, Boolean, Maybe
from amino.boolean import false

from ribosome.trans.handler import TransHandler

from myo.data.command import Command


def cannot_run(cmd: Command) -> Boolean:
    return false


class MyoComponent(Dat['MyoComponent']):

    @staticmethod
    def cons(
            run: TransHandler=None,
            can_run: Callable[[Command], Boolean]=None
    ) -> 'MyoComponent':
        return MyoComponent(Maybe.check(run), can_run or cannot_run)

    def __init__(self, run: Maybe[TransHandler], can_run: Callable[[Command], Boolean]) -> None:
        self.run = run
        self.can_run = can_run

__all__ = ('MyoComponent',)
