from typing import Callable, Any

from amino import Dat, Maybe, Nothing

from ribosome.config.component import Component, ComponentData
from ribosome.compute.program import Program

from myo.env import Env
from myo.ui.ui import Ui
from myo.command.run_task import RunTask
from myo.data.info import InfoWidget
from myo.data.command import Pid


def no_handler(*a: Any, **kw: Any) -> Maybe[Program]:
    return Nothing


class MyoComponent(Dat['MyoComponent']):

    @staticmethod
    def cons(
            run: Callable[[RunTask], Maybe[Program[Pid]]]=None,
            create_vim_pane: Callable[[], Maybe[Program]]=None,
            info: Program[InfoWidget]=None,
            ui: Ui=None,
            init: Program[None]=None,
            quit: Program[None]=None,
    ) -> 'MyoComponent':
        return MyoComponent(
            run or no_handler,
            create_vim_pane or no_handler,
            Maybe.optional(info),
            Maybe.optional(ui),
            Maybe.optional(init),
            Maybe.optional(quit),
        )

    def __init__(
            self,
            run: Callable[[RunTask], Maybe[Program[Pid]]],
            create_vim_pane: Callable[[RunTask], Maybe[Program]],
            info: Maybe[Program[InfoWidget]],
            ui: Maybe[Ui],
            init: Maybe[Program[None]],
            quit: Maybe[Program[None]],
    ) -> None:
        self.run = run
        self.create_vim_pane = create_vim_pane
        self.info = info
        self.ui = ui
        self.init = init
        self.quit = quit


Comp = Component[ComponentData, MyoComponent]

__all__ = ('MyoComponent',)
