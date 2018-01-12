from amino import List

from ribosome.dispatch.component import Component

from myo.components.tmux.trans.run import run_command, tmux_can_run
from myo.config.component import MyoComponent
from myo.tmux.data.tmux import TmuxData


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
