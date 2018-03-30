from typing import Callable, Any

from amino import Dat, Maybe, Nothing

from ribosome.trans.handler import Trans
from ribosome.dispatch.component import Component, ComponentData

from myo.env import Env
from myo.ui.ui import Ui
from myo.command.run_task import RunTask
from myo.data.info import InfoWidget


def no_handler(*a: Any, **kw: Any) -> Maybe[Trans]:
    return Nothing


class MyoComponent(Dat['MyoComponent']):

    @staticmethod
    def cons(
            run: Callable[[RunTask], Maybe[Trans]]=None,
            create_vim_pane: Callable[[], Maybe[Trans]]=None,
            info: Trans[InfoWidget]=None,
            ui: Ui=None,
            init: Trans[None]=None,
    ) -> 'MyoComponent':
        return MyoComponent(
            run or no_handler,
            create_vim_pane or no_handler,
            Maybe.optional(info),
            Maybe.optional(ui),
            Maybe.optional(init),
        )

    def __init__(
            self,
            run: Callable[[RunTask], Maybe[Trans]],
            create_vim_pane: Callable[[RunTask], Maybe[Trans]],
            info: Maybe[Trans[InfoWidget]],
            ui: Maybe[Ui],
            init: Maybe[Trans[None]],
    ) -> None:
        self.run = run
        self.create_vim_pane = create_vim_pane
        self.info = info
        self.ui = ui
        self.init = init


Comp = Component[Env, ComponentData, MyoComponent]

__all__ = ('MyoComponent',)
