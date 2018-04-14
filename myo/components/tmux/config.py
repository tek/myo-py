from amino import List, Just, Nothing, Maybe

from ribosome.config.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.compute.prog import Program

from chiasma.data.tmux import TmuxData

from myo.components.tmux.compute.run import run_command, tmux_can_run
from myo.config.component import MyoComponent
from myo.ui.ui import Ui
from myo.components.tmux.compute.owns_pane import tmux_owns_pane
from myo.components.tmux.compute.render import tmux_render
from myo.command.run_task import RunTask
from myo.components.tmux.compute.create_vim_pane import create_vim_pane
from myo.components.tmux.compute.info import tmux_info
from myo.components.tmux.compute.quit import tmux_quit
from myo.env import Env


def run_handler_for(task: RunTask) -> Maybe[Program]:
    return Just(run_command) if tmux_can_run(task) else Nothing


tmux_ui = Ui.cons(tmux_owns_pane, tmux_render)
tmux: Component[Env, TmuxData, MyoComponent] = Component.cons(
    'tmux',
    state_type=TmuxData,
    request_handlers=List(
        RequestHandler.trans_function(tmux_render)(),
        RequestHandler.trans_function(run_command)(),
        RequestHandler.trans_function(create_vim_pane)(),
        RequestHandler.trans_function(tmux_info)(),
        RequestHandler.trans_function(tmux_quit)(),
    ),
    config=MyoComponent.cons(
        run_handler_for,
        lambda: Just(create_vim_pane),
        info=tmux_info,
        ui=tmux_ui,
        quit=tmux_quit,
    ),
)

__all__ = ('tmux',)
