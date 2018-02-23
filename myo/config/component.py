from typing import Callable

from amino import Dat, Boolean, Maybe
from amino.boolean import false

from ribosome.trans.handler import TransHandler
from ribosome.dispatch.component import Component, ComponentData

from myo.data.command import Command
from myo.env import Env
from myo.ui.ui import Ui


def cannot_run(cmd: Command) -> Boolean:
    return false


class MyoComponent(Dat['MyoComponent']):

    @staticmethod
    def cons(
            run: TransHandler=None,
            can_run: Callable[[Command], Boolean]=None,
            ui: Ui=None,
    ) -> 'MyoComponent':
        return MyoComponent(Maybe.check(run), can_run or cannot_run, Maybe.check(ui))

    def __init__(self, run: Maybe[TransHandler], can_run: Callable[[Command], Boolean], ui: Maybe[Ui]) -> None:
        self.run = run
        self.can_run = can_run
        self.ui = ui


Comp = Component[Env, ComponentData, MyoComponent]

__all__ = ('MyoComponent',)
