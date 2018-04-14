from ribosome.test.integration.run import RequestHelper
from ribosome.config.config import Config

from chiasma.data.view_tree import ViewTree
from chiasma.data.session import Session
from chiasma.data.window import Window as TWindow
from chiasma.test.tmux_spec import tmux_spec_socket
from chiasma.io.compute import TmuxIO
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.data.pane import Pane as TPane

from amino import List, __, Map, do, Do, L, _, Nil
from amino.boolean import true
from amino.lenses.lens import lens
from amino.test import temp_dir

from myo.ui.data.view import Layout, Pane
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.settings import MyoSettings
from myo.ui.pane import map_panes_in_spaces
from myo.components.command.config import command
from myo.components.core.config import core


tmux_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(core=core, ui=ui, tmux=tmux, command=command),
    core_components=List('core'),
)


def tmux_spec_helper(extra: List[str]) -> RequestHelper:
    return RequestHelper.strict(
        tmux_spec_config,
        'ui',
        'tmux',
        *extra,
        vars=Map(
            myo_tmux_socket=tmux_spec_socket,
            myo_state_dir=str(temp_dir('history', 'state')),
        ),
    )


def init_tmux_data(layout: ViewTree[Layout, Pane], extra: List[str]=Nil) -> RequestHelper:
    window = Window.cons('win', layout=layout)
    space = Space.cons('spc', List(window))
    return (
        window,
        space,
        tmux_spec_helper(extra)
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


def two_panes(extra: List[str]=Nil) -> RequestHelper[MyoSettings, Env, MyoComponent]:
    layout = ViewTree.layout(
        Layout.cons('root', vertical=true),
        List(
            ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(min_size=10, max_size=90))),
            ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons(weight=0.5, position=12))),
        )
    )
    window, space, helper = init_tmux_data(layout, extra)
    return helper.mod.state(
        __
        .modify_component_data(
            'tmux',
            __.set.panes(List(TPane.cons('one', id=0), TPane.cons('two', id=1)))
        )
        .modify_component_data(
            'ui',
            __.mod.spaces(L(map_panes_in_spaces)(lambda a: True, lens.open.set(true), _))
        )
    )


@do(TmuxIO[RequestHelper[MyoSettings, Env, MyoComponent]])
def two_open_panes() -> Do:
    yield TmuxIO.write('split-window')
    yield TmuxIO.pure(two_panes())


__all__ = ('tmux_spec_config', 'init_tmux_data', 'tmux_spec_helper')
