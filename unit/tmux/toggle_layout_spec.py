from kallikrein import Expectation
from kallikrein.matchers.comparison import less_equal, greater
from kallikrein.matcher import Matcher

from ribosome.test.unit import unit_test

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from myo.components.tmux.data import TmuxData
from chiasma.data.pane import Pane as TPane
from chiasma.commands.pane import pane_width

from amino import do, Do, List
from ribosome.test.prog import request
from ribosome.nvim.io.state import NS

from myo.config.plugin_state import MyoState
from myo.ui.data.view import Layout, Pane

from test.klk.tmux import tmux_await_k

from unit._support.tmux import tmux_default_test_config, init_tmux_data

layout: ViewTree[Layout, Pane] = ViewTree.layout(
    Layout.cons('root', vertical=False),
    List(
        ViewTree.layout(
            Layout.cons('vim', vertical=True),
            List(
                ViewTree.pane(Pane.cons('one', open=True)),
            ),
        ),
        ViewTree.layout(
            Layout.cons('make', vertical=True),
            List(
                ViewTree.pane(Pane.cons('two')),
                ViewTree.pane(Pane.cons('three')),
            ),
        )
    )
)


def add_tmux_pane(data: TmuxData) -> TmuxData:
    return data.set.panes(List(TPane.cons('one', id=0)))


def await_pane_width(matcher: Matcher[int]) -> NS[MyoState, Expectation]:
    return NS.lift(tmux_await_k(matcher, pane_width, 1))


@do(NS[MyoState, Expectation])
def toggle_layout_spec() -> Do:
    window, space = yield init_tmux_data(layout)
    yield NS.modify(lambda a: a.modify_component_data('tmux', add_tmux_pane))
    yield request('open_pane', 'two')
    yield request('open_pane', 'three')
    initial_size = yield await_pane_width(greater(3))
    yield request('toggle_layout', 'make')
    minimized_size = yield await_pane_width(less_equal(3))
    yield request('toggle_layout', 'make')
    restored_size = yield await_pane_width(greater(3))
    return initial_size & minimized_size & restored_size


class ToggleLayoutSpec(TmuxSpec):
    '''
    toggle a layout $toggle_layout
    '''

    def toggle_layout(self) -> Expectation:
        return unit_test(tmux_default_test_config(), toggle_layout_spec)


__all__ = ('ToggleLayoutSpec',)
