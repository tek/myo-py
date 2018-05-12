from kallikrein import Expectation
from kallikrein.matchers.comparison import less_equal, greater

from ribosome.test.unit import unit_test

from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import all_panes
from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from chiasma.data.tmux import TmuxData
from chiasma.data.pane import Pane as TPane

from amino import do, Do, List
from ribosome.test.prog import request
from ribosome.nvim.io.state import NS

from myo.config.plugin_state import MyoState
from myo.ui.data.view import Layout, Pane

from test.klk.tmux import tmux_await_k

from unit._support.tmux import tmux_default_test_config, init_tmux_data

layout: ViewTree[Layout, Pane] = ViewTree.layout(
    Layout.cons('root', vertical=True),
    List(
        ViewTree.pane(Pane.cons('one', open=True)),
        ViewTree.pane(Pane.cons('two')),
    )
)

def add_tmux_pane(data: TmuxData) -> TmuxData:
    return data.set.panes(List(TPane.cons('one', id=0), TPane.cons('two', id=1)))


@do(TmuxIO[int])
def pane_one_size() -> Do:
    panes = yield all_panes()
    pane = yield TmuxIO.from_maybe(panes.find(lambda a: a.id == 1), 'pane `one` not found')
    return pane.height


@do(NS[MyoState, Expectation])
def toggle_pane_spec() -> Do:
    window, space = yield init_tmux_data(layout)
    yield NS.modify(lambda a: a.modify_component_data('tmux', add_tmux_pane))
    yield request('toggle_pane', 'two')
    initial_size = yield NS.lift(tmux_await_k(greater(3), pane_one_size))
    yield request('toggle_pane', 'two')
    minimized_size = yield NS.lift(tmux_await_k(less_equal(3), pane_one_size))
    yield request('toggle_pane', 'two')
    restored_size = yield NS.lift(tmux_await_k(greater(3), pane_one_size))
    return initial_size & minimized_size & restored_size


class TogglePaneSpec(TmuxSpec):
    '''
    toggle a tmux pane $toggle_pane
    '''

    def toggle_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), toggle_pane_spec)


__all__ = ('TogglePaneSpec',)
