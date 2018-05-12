from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import all_panes

from amino import do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import doautocmd, nvim_command
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.nvim.io.api import N

from test.klk.tmux import tmux_await_k

from unit._support.tmux import tmux_default_test_config

test_config = tmux_default_test_config()


@do(NvimIO[Expectation])
def vim_leave_spec() -> Do:
    yield nvim_command('MyoOpenPane', 'make')
    yield N.sleep(1)
    yield tmux_await_k(have_length(2), all_panes)
    yield doautocmd('VimLeave')
    yield N.sleep(1)
    yield tmux_await_k(have_length(1), all_panes)


class QuitSpec(SpecBase):
    '''
    close all ui elements when leaving vim $vim_leave
    '''

    def vim_leave(self) -> Expectation:
        return tmux_plugin_test(test_config, vim_leave_spec)


__all__ = ('QuitSpec',)
