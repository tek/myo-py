from amino import List

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from chiasma.data.tmux import TmuxData

from myo.components.tmux.trans.run import run_command, tmux_can_run, run_command
from myo.config.component import MyoComponent
from myo.ui.ui import Ui
from myo.components.tmux.trans.owns_pane import tmux_owns_pane
from myo.components.tmux.trans.render import tmux_render


ui = Ui.cons(tmux_owns_pane, tmux_render)


tmux = Component.cons(
    'tmux',
    state_ctor=TmuxData.cons,
    request_handlers=List(
        RequestHandler.trans_function(tmux_render)(),
        RequestHandler.trans_function(run_command)(),
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(run_command, tmux_can_run, ui),
)

__all__ = ('tmux',)
