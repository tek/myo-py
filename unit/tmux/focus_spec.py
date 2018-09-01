from kallikrein import Expectation
from kallikrein.matchers import equal

from chiasma.test.tmux_spec import TmuxSpec

from amino import do, Do

from ribosome.test.unit import unit_test
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request

from test.tmux import tmux_default_test_config, two_panes, pane_focus
from test.klk.tmux import tmux_await_k

from myo.config.plugin_state import MyoState


@do(NS[MyoState, Expectation])
def focus_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield request('open_pane', 'two', '{}')
    yield request('focus', 'two')
    yield NS.lift(tmux_await_k(equal(True), pane_focus, 1))


class FocusPaneSpec(TmuxSpec):
    '''
    focus a pane $focus
    '''

    def focus(self) -> Expectation:
        return unit_test(tmux_default_test_config(), focus_spec)


__all__ = ('FocusPaneSpec',)
