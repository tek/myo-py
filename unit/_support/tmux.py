from typing import Tuple, Any

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

from ribosome.config.config import Config
from ribosome.nvim.io.state import NS
from ribosome.test.config import TestConfig

from myo.ui.data.view import Layout, Pane
from myo.ui.data.window import Window
from myo.ui.data.space import Space
from myo.env import Env
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.ui.pane import map_panes_in_spaces
from myo.components.command.config import command
from myo.components.core.config import core
from myo.config.plugin_state import MyoState
from myo.tmux.io import tmux_to_nvim


tmux_spec_config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(core=core, ui=ui, tmux=tmux, command=command),
    core_components=List('core'),
)
vars = Map(
    myo_tmux_socket=tmux_spec_socket,
    myo_state_dir=str(temp_dir('history', 'state')),
)


def tmux_test_config(config: Config, components: List[str]=Nil, extra_vars: Map[str, Any]=Map(), **kw: Any
                     ) -> TestConfig:
    return TestConfig.cons(config, vars=vars ** extra_vars, components=List('ui', 'tmux') + components, **kw)


def tmux_default_test_config(components: List[str]=Nil, extra_vars: Map[str, Any]=Map(), **kw: Any) -> TestConfig:
    return tmux_test_config(tmux_spec_config, components, extra_vars, **kw)


@do(NS[MyoState, Tuple[Window, Space]])
def init_tmux_data(layout: ViewTree[Layout, Pane]) -> Do:
    window = Window.cons('win', layout=layout)
    space = Space.cons('spc', List(window))
    yield NS.modify(
        __
        .modify_component_data('ui', __.append1.spaces(space))
        .modify_component_data(
            'tmux',
            __
            .append1.sessions(Session.cons(space.ident, id=0))
            .append1.windows(TWindow.cons(window.ident, id=0))
        )
    )
    return window, space


@do(NS[MyoState, Tuple[Window, Space]])
def two_panes() -> Do:
    layout = ViewTree.layout(
        Layout.cons('root', vertical=true),
        List(
            ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(min_size=10, max_size=90))),
            ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons(weight=0.5, position=12))),
        )
    )
    window, space = yield init_tmux_data(layout)
    yield NS.modify(
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
    return window, space


@do(NS[MyoState, Tuple[Window, Space]])
def two_open_panes() -> Do:
    yield NS.lift(tmux_to_nvim(TmuxIO.write('split-window')))
    yield two_panes()


__all__ = ('tmux_spec_config', 'init_tmux_data', 'tmux_default_test_config', 'two_panes', 'two_open_panes',
           'tmux_test_config',)
