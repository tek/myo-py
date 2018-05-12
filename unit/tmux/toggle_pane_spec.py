from kallikrein import k, Expectation
from kallikrein.matchers.comparison import less_equal, greater

from ribosome.test.unit import unit_test

from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import all_panes
from chiasma.test.tmux_spec import TmuxSpec

from amino import do, Do
from ribosome.test.prog import request
from ribosome.nvim.io.state import NS

from myo.config.plugin_state import MyoState

from test.klk.tmux import tmux_await_k

from unit._support.tmux import tmux_default_test_config, two_panes


@do(TmuxIO[int])
def pane_one_size() -> Do:
    panes = yield all_panes()
    pane = yield TmuxIO.from_maybe(panes.find(lambda a: a.id == 1), 'pane `one` not found')
    return pane.height


@do(NS[MyoState, Expectation])
def toggle_pane_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one')
    yield request('open_pane', 'two')
    yield request('toggle_pane', 'two')
    minimized_size = yield NS.lift(tmux_await_k(less_equal(3), pane_one_size))
    yield request('toggle_pane', 'two')
    restored_size = yield NS.lift(tmux_await_k(greater(3), pane_one_size))
    return minimized_size & restored_size


class TogglePaneSpec(TmuxSpec):
    '''
    toggle a tmux pane $toggle_pane
    '''

    def toggle_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), toggle_pane_spec)


__all__ = ('TogglePaneSpec',)
