from kallikrein import Expectation
from kallikrein.matchers.length import have_length

from amino import List, do, Do, Map
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.test.klk.matchers.buffer import current_buffer_matches

from myo import myo_config

from test.tmux import tmux_test_config

vars = Map(
    myo_vim_tmux_pane=0,
    myo_auto_jump=0,
)
test_config = tmux_test_config(myo_config, components=List('command'), extra_vars=vars)


@do(NvimIO[Expectation])
def info_spec() -> Do:
    yield nvim_command('MyoInfo')
    yield current_buffer_matches(have_length(12))


class InfoSpec(SpecBase):
    '''show information $info
    '''

    def info(self) -> Expectation:
        return tmux_plugin_test(test_config, info_spec)


__all__ = ('InfoSpec',)
