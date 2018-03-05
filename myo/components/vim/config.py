from amino import List, Dat, Maybe, Just, Nothing

from ribosome.dispatch.component import Component
from ribosome.trans.handler import FreeTrans

from myo.components.vim.trans.run import run_command, vim_can_run
from myo.config.component import MyoComponent
from myo.command.run_task import RunTask


def run_handler_for(task: RunTask) -> Maybe[FreeTrans]:
    return Just(run_command) if vim_can_run(task) else Nothing


class VimData(Dat['VimData']):

    @staticmethod
    def cons(
    ) -> 'VimData':
        return VimData(
        )

    def __init__(self) -> None:
        pass


vim = Component.cons(
    'vim',
    state_ctor=VimData.cons,
    request_handlers=List(
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(run_handler_for),
)

__all__ = ('vim',)
