from amino import List, Dat

from ribosome.dispatch.component import Component

from myo.components.tmux.trans.run import run_command, tmux_can_run
from myo.config.component import MyoComponent


class TmuxData(Dat['TmuxData']):

    @staticmethod
    def cons(
    ) -> 'TmuxData':
        return TmuxData(
        )

    def __init__(self) -> None:
        pass


tmux = Component.cons(
    'tmux',
    state_ctor=TmuxData.cons,
    request_handlers=List(
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(run_command, tmux_can_run),
)

__all__ = ('tmux',)
