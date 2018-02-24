from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from chiasma.data.view_tree import ViewTree
from chiasma.data.session import Session
from chiasma.data.window import Window as TWindow
from chiasma.test.tmux_spec import tmux_spec_socket

from amino import List, __, Map

from myo.ui.data.view import Layout, Pane
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui


tmux_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(ui=ui, tmux=tmux),
    component_config_type=MyoComponent,
)
tmux_spec_helper = DispatchHelper.cons(tmux_spec_config, 'ui', 'tmux', vars=dict(myo_tmux_socket=tmux_spec_socket))


def init_tmux_data(layout: ViewTree[Layout, Pane]) -> DispatchHelper:
    window = Window.cons('win', layout=layout)
    space = Space.cons('spc', List(window))
    return (
        window,
        space,
        tmux_spec_helper
        .mod.state(
            __
            .modify_component_data('ui', __.append1.spaces(space))
            .modify_component_data(
                'tmux',
                __
                .append1.sessions(Session.cons(space.ident, id=0))
                .append1.windows(TWindow.cons(window.ident, id=0))
            )
        )
    )


__all__ = ('tmux_spec_config', 'init_tmux_data', 'tmux_spec_helper')
