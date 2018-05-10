from kallikrein import Expectation
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO

from amino import do, Do

from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from myo.config.plugin_state import MyoState

from test.klk.tmux import tmux_await_k

from unit._support.tmux import two_open_panes, tmux_default_test_config


@do(NS[MyoState, Expectation])
def close_pane_spec() -> Do:
    yield two_open_panes()
    yield request('close_pane', 'one')
    yield NS.lift(tmux_await_k(have_length(1), TmuxIO.read, 'list-panes'))


class ClosePaneSpec(TmuxSpec):
    '''
    close a tmux pane $close_pane
    '''

    def close_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), close_pane_spec)


__all__ = ('ClosePaneSpec',)
