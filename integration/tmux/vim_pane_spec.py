from kallikrein import Expectation
from kallikrein.matchers.length import have_length

from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import all_panes

from amino import do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command
from ribosome.nvim.io.api import N
from ribosome.test.integration.tmux import tmux_plugin_test

from myo import myo_config

from test.klk.tmux import tmux_await_k

from unit._support.tmux import tmux_test_config


@do(NvimIO[Expectation])
def open_make_spec() -> Do:
    yield nvim_command('MyoOpenPane', 'make')
    yield tmux_await_k(have_length(2), all_panes)


test_config = tmux_test_config(myo_config)


class VimPaneSpec(SpecBase):
    '''
    open the pane `make` $open_make
    '''

    def open_make(self) -> Expectation:
        return tmux_plugin_test(test_config, open_make_spec)


__all__ = ('VimPaneSpec',)
