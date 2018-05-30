from amino import List, Just, Nothing, Maybe

from ribosome.config.component import Component
from ribosome.compute.program import Program
from ribosome.rpc.api import rpc

from myo.components.tmux.data import TmuxData

from myo.components.tmux.compute.run import tmux_run_command, tmux_can_run
from myo.config.component import MyoComponent
from myo.ui.ui import Ui
from myo.components.tmux.compute.owns_pane import tmux_owns_view
from myo.components.tmux.compute.render import tmux_render
from myo.command.run_task import RunTask
from myo.components.tmux.compute.create_vim_pane import create_vim_pane
from myo.components.tmux.compute.info import tmux_info
from myo.components.tmux.compute.quit import tmux_quit


def run_handler_for(task: RunTask) -> Maybe[Program]:
    return Just(tmux_run_command) if tmux_can_run(task) else Nothing


def create_vim_pane_handler() -> Maybe[Program]:
    return Just(create_vim_pane)


tmux_ui = Ui.cons(tmux_owns_view, tmux_render)
tmux: Component[TmuxData, MyoComponent] = Component.cons(
    'tmux',
    state_type=TmuxData,
    rpc=List(
        rpc.write(tmux_render),
        rpc.write(tmux_info),
        rpc.write(tmux_quit),
    ),
    config=MyoComponent.cons(
        run_handler_for,
        create_vim_pane_handler,
        info=tmux_info,
        ui=tmux_ui,
        quit=tmux_quit,
    ),
)

__all__ = ('tmux',)
