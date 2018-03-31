from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import tmux_spec_socket
from chiasma.io.compute import TmuxIO

from amino import List, do, Do

from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.data import Buffer
from ribosome.nvim.api.command import nvim_command
from ribosome.test.integration.klk import later

from integration._support.spec import TmuxDefaultSpec


class DefaultUiSpec(TmuxDefaultSpec):
    '''
    open the pane `make` $open_make
    '''

    def _pre_start(self) -> None:
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('vim_tmux_pane', 0)
            yield variable_set_prefixed('tmux_socket', tmux_spec_socket)
        run().unsafe(self.vim)
        super()._pre_start()

    def open_make(self) -> Expectation:
        @do(NvimIO[List[Buffer]])
        def run() -> Do:
            yield nvim_command('MyoOpenPane', 'make')
        run().unsafe(self.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(2)))


__all__ = ('DefaultUiSpec',)
