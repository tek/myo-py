from kallikrein import Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers import equal

from chiasma.commands.pane import all_panes, pane_width

from amino import do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command
from ribosome.test.integration.tmux import tmux_plugin_test

from myo import myo_config
from myo.settings import vim_pane_geometry

from test.klk.tmux import tmux_await_k

from test.tmux import tmux_test_config


@do(NvimIO[Expectation])
def open_make_spec() -> Do:
    yield nvim_command('MyoOpenPane', 'make')
    yield tmux_await_k(have_length(2), all_panes)


def set_vim_geometry() -> NvimIO[None]:
    return vim_pane_geometry.update(dict(fixed_size=125))


@do(NvimIO[Expectation])
def size_spec() -> Do:
    yield nvim_command('MyoOpenPane', 'make')
    yield tmux_await_k(equal(125), pane_width, 0)


test_config = tmux_test_config(myo_config)


class VimPaneSpec(SpecBase):
    '''
    open the pane `make` $open_make
    control the size of the vim pane $size
    '''

    def open_make(self) -> Expectation:
        return tmux_plugin_test(test_config, open_make_spec)

    def size(self) -> Expectation:
        return tmux_plugin_test(test_config.copy(pre=set_vim_geometry), size_spec)


__all__ = ('VimPaneSpec',)
