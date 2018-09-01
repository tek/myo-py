from kallikrein import Expectation
from kallikrein.matchers import equal
from kallikrein.matchers.comparison import less_equal

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import pane_height, pane_width

from amino import do, Do

from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from myo.config.plugin_state import MyoState

from test.klk.tmux import tmux_await_k

from test.tmux import (two_open_panes, tmux_default_test_config, pane_left_vertical_right,
                                vertical_left_vertical_right)


@do(NS[MyoState, Expectation])
def simple_spec() -> Do:
    yield two_open_panes()
    yield request('minimize_pane', 'one')
    yield NS.lift(tmux_await_k(equal(2), pane_height, 0))


@do(NS[MyoState, Expectation])
def pane_stack_spec() -> Do:
    yield pane_left_vertical_right()
    yield request('open_pane', 'two')
    yield request('open_pane', 'three')
    yield request('minimize_pane', 'three')
    yield NS.lift(tmux_await_k(less_equal(3), pane_height, 2))


@do(NS[MyoState, Expectation])
def two_stacks_spec() -> Do:
    yield vertical_left_vertical_right()
    yield request('open_pane', 'two')
    yield request('toggle_layout', 'right')
    yield NS.lift(tmux_await_k(less_equal(3), pane_width, 1))


class MinimizePaneSpec(TmuxSpec):
    '''
    minimize a tmux pane
    simple $simple
    pane on left, vertical stack on right $pane_stack
    two vertical stacks $two_stacks
    '''

    def simple(self) -> Expectation:
        return unit_test(tmux_default_test_config(), simple_spec)

    def pane_stack(self) -> Expectation:
        return unit_test(tmux_default_test_config(), pane_stack_spec)

    def two_stacks(self) -> Expectation:
        return unit_test(tmux_default_test_config(), two_stacks_spec)


__all__ = ('MinimizePaneSpec',)
