from amino import List, Just, Nothing, Maybe

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.trans.handler import TransHandler

from chiasma.data.tmux import TmuxData

from myo.components.tmux.trans.run import run_command, tmux_can_run
from myo.config.component import MyoComponent
from myo.ui.ui import Ui
from myo.components.tmux.trans.owns_pane import tmux_owns_pane
from myo.components.tmux.trans.render import tmux_render
from myo.command.run_task import RunTask
from myo.components.tmux.trans.create_vim_pane import create_vim_pane


def run_handler_for(task: RunTask) -> Maybe[TransHandler]:
    return Just(run_command) if tmux_can_run(task) else Nothing


ui = Ui.cons(tmux_owns_pane, tmux_render)
tmux = Component.cons(
    'tmux',
    state_ctor=TmuxData.cons,
    request_handlers=List(
        RequestHandler.trans_function(tmux_render)(),
        RequestHandler.trans_function(run_command)(),
        RequestHandler.trans_function(create_vim_pane)(),
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(run_handler_for, lambda: Just(create_vim_pane), ui),
)

__all__ = ('tmux',)
