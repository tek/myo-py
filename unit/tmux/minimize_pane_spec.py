from kallikrein import Expectation, kf, Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers import equal

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import pane
from chiasma.io.compute import TmuxIO

from amino import do, Do

from ribosome.test.integration.klk import later
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from myo.config.plugin_state import MyoState

from test.klk.tmux import tmux_await_k

from unit._support.tmux import two_open_panes, tmux_default_test_config


@do(TmuxIO[int])
def pane_height(id: int) -> Do:
    p = yield pane(0)
    return p.height


@do(NS[MyoState, Expectation])
def minimize_pane_spec() -> Do:
    yield two_open_panes()
    yield request('minimize_pane', 'one')
    yield NS.lift(tmux_await_k(equal(2), pane_height, 0))


class MinimizePaneSpec(TmuxSpec):
    '''
    minimize a tmux pane $minimize_pane
    '''

    def minimize_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), minimize_pane_spec)


__all__ = ('MinimizePaneSpec',)
