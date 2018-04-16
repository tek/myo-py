from amino import List, Dat, Maybe, Just, Nothing

from ribosome.config.component import Component
from ribosome.compute.program import Program

from myo.components.vim.compute.run import run_command, vim_can_run
from myo.config.component import MyoComponent
from myo.command.run_task import RunTask


def run_handler_for(task: RunTask) -> Maybe[Program]:
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
    state_type=VimData,
    request_handlers=List(
    ),
    config=MyoComponent.cons(run_handler_for),
)

__all__ = ('vim',)
