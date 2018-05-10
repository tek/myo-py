from typing import TypeVar

from kallikrein import Expectation
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO

from test.klk.tmux import tmux_await_k

from amino import do, Do

from ribosome.test.unit import unit_test
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request

from myo.config.plugin_state import MyoPluginState

from unit._support.tmux import two_panes, tmux_default_test_config


@do(NS[MyoPluginState, Expectation])
def open_pane_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield request('open_pane', 'two', '{}')
    yield NS.lift(tmux_await_k(have_length(2), TmuxIO.read, 'list-panes'))


class OpenPaneSpec(TmuxSpec):
    '''
    open a tmux pane $open_pane
    '''

    def open_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), open_pane_spec)


__all__ = ('OpenPaneSpec',)
