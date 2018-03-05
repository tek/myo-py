from typing import Callable, Any

from amino import Dat, Maybe, Nothing

from ribosome.trans.handler import FreeTrans
from ribosome.dispatch.component import Component, ComponentData

from myo.env import Env
from myo.ui.ui import Ui
from myo.command.run_task import RunTask


def no_handler(*a: Any, **kw: Any) -> Maybe[FreeTrans]:
    return Nothing


class MyoComponent(Dat['MyoComponent']):

    @staticmethod
    def cons(
            run: Callable[[RunTask], Maybe[FreeTrans]]=None,
            create_vim_pane: Callable[[], Maybe[FreeTrans]]=None,
            ui: Ui=None,
    ) -> 'MyoComponent':
        return MyoComponent(
            run or no_handler,
            create_vim_pane or no_handler,
            Maybe.check(ui),
        )

    def __init__(
            self,
            run: Callable[[RunTask], Maybe[FreeTrans]],
            create_vim_pane: Callable[[RunTask], Maybe[FreeTrans]],
            ui: Maybe[Ui],
    ) -> None:
        self.run = run
        self.create_vim_pane = create_vim_pane
        self.ui = ui


Comp = Component[Env, ComponentData, MyoComponent]

__all__ = ('MyoComponent',)
