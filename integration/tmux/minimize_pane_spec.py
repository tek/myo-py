from kallikrein import k, Expectation

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command
from ribosome.test.config import TestConfig
from ribosome.nvim.io.api import N
from ribosome.test.integration.tmux import tmux_plugin_test

from amino.test.spec import SpecBase
from amino import do, Do

from myo import myo_config


@do(NvimIO[Expectation])
def minimize_pane_spec() -> Do:
    yield nvim_command('MyoCreatePane', '{ "layout": "make", "name": "pane"}')
    yield nvim_command('MyoTogglePane', 'pane')
    yield nvim_command('MyoTogglePane', 'pane')
    yield N.sleep(1)
    return k(1) == 1


test_config = TestConfig.cons(myo_config)


class MinimizePaneSpec(SpecBase):
    '''
    minimize a pane $minimize_pane
    '''

    def minimize_pane(self) -> Expectation:
        return tmux_plugin_test(test_config, minimize_pane_spec)


__all__ = ('MinimizePaneSpec',)
