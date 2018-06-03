from typing import Tuple, Any, Callable

from chiasma.data.view_tree import ViewTree
from chiasma.data.session import Session
from chiasma.data.window import Window as TWindow
from chiasma.test.tmux_spec import tmux_spec_socket
from chiasma.io.compute import TmuxIO
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.data.pane import Pane as TPane
from chiasma.data.tmux import Views
from myo.components.tmux.data import TmuxData

from amino import List, __, Map, do, Do, Nil
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
from myo.ui.data.ui_data import UiData


tmux_spec_config: Config = Config.cons(
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


def tmux_test_config(
        config: Config=tmux_spec_config,
        components: List[str]=Nil,
        extra_vars: Map[str, Any]=Map(),
        **kw: Any,
) -> TestConfig:
    return TestConfig.cons(config, vars=vars ** extra_vars, components=List('ui', 'tmux') + components, **kw)


def tmux_default_test_config(components: List[str]=Nil, extra_vars: Map[str, Any]=Map(), **kw: Any) -> TestConfig:
    return tmux_test_config(tmux_spec_config, components, extra_vars, **kw)


def update_data(name: str, update: Callable[[Any], Any]) -> NS[MyoState, None]:
    return NS.modify(lambda a: a.modify_component_data(name, update))


def update_ui_data(update: Callable[[UiData], UiData]) -> NS[MyoState, None]:
    return update_data('ui', update)


def update_tmux_data(update: Callable[[TmuxData], TmuxData]) -> NS[MyoState, None]:
    return update_data('tmux', update)


def update_views(update: Callable[[Views], Views]) -> NS[MyoState, None]:
    return update_tmux_data(lens.views.modify(update))


def set_panes(panes: List[TPane]) -> NS[MyoState, None]:
    return update_tmux_data(lambda a: a.set.panes(panes))


@do(NS[MyoState, Tuple[Window, Space]])
def init_tmux_data(layout: ViewTree[Layout, Pane]) -> Do:
    window = Window.cons('win', layout=layout)
    space = Space.cons('spc', List(window))
    yield update_ui_data(__.append1.spaces(space))
    yield update_views(
        __
        .append1.sessions(Session.cons(space.ident, id=0))
        .append1.windows(TWindow.cons(window.ident, id=0))
    )
    return window, space


two_pane_layout = ViewTree.layout(
    Layout.cons('root', vertical=true),
    List(
        ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(min_size=10, max_size=90))),
        ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons(weight=0.5, position=12))),
    )
)


@do(NS[MyoState, Tuple[Window, Space]])
def two_panes() -> Do:
    window, space = yield init_tmux_data(two_pane_layout)
    yield update_views(lens.panes.set(List(TPane.cons('one', id=0), TPane.cons('two', id=1))))
    return window, space


@do(NS[MyoState, Tuple[Window, Space]])
def two_open_panes() -> Do:
    yield NS.lift(tmux_to_nvim(TmuxIO.write('split-window')))
    yield two_panes()
    yield update_ui_data(lens.spaces.modify(map_panes_in_spaces(lambda a: True, lens.open.set(true))))


pane_left_vertical_right_layout: ViewTree[Layout, Pane] = ViewTree.layout(
    Layout.cons('root', vertical=False),
    List(
        ViewTree.pane(Pane.cons('one', open=True)),
        ViewTree.layout(
            Layout.cons('make', vertical=True),
            List(
                ViewTree.pane(Pane.cons('two')),
                ViewTree.pane(Pane.cons('three')),
            ),
        )
    )
)


@do(NS[MyoState, Tuple[Window, Space]])
def pane_left_vertical_right() -> Do:
    window, space = yield init_tmux_data(pane_left_vertical_right_layout)
    yield set_panes(List(TPane.cons('one', id=0)))
    return window, space


vertical_left_vertical_right_layout: ViewTree[Layout, Pane] = ViewTree.layout(
    Layout.cons('root', vertical=False),
    List(
        ViewTree.layout(
            Layout.cons('left', vertical=True),
            List(
                ViewTree.pane(Pane.cons('one', open=True)),
            ),
        ),
        ViewTree.layout(
            Layout.cons('right', vertical=True),
            List(
                ViewTree.pane(Pane.cons('two')),
            ),
        )
    )
)


@do(NS[MyoState, Tuple[Window, Space]])
def vertical_left_vertical_right() -> Do:
    window, space = yield init_tmux_data(vertical_left_vertical_right_layout)
    yield set_panes(List(TPane.cons('one', id=0)))
    return window, space


__all__ = ('tmux_spec_config', 'init_tmux_data', 'tmux_default_test_config', 'two_panes', 'two_open_panes',
           'tmux_test_config', 'pane_left_vertical_right', 'vertical_left_vertical_right',)
