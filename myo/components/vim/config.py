from amino import List, Dat

from ribosome.dispatch.component import Component

from myo.components.vim.trans.run import run_command, vim_can_run
from myo.config.component import MyoComponent


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
    config=MyoComponent.cons(run_command, vim_can_run),
)

__all__ = ('vim',)
