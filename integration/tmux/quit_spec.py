from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import tmux_spec_socket
from chiasma.io.compute import TmuxIO

from amino import List, do, Do

from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.data import Buffer
from ribosome.test.integration.klk import later
from ribosome.nvim.api.command import doautocmd, nvim_command

from integration._support.spec import TmuxDefaultSpec


class QuitSpec(TmuxDefaultSpec):
    '''
    close all ui elements when leaving vim $vim_leave
    '''

    def _pre_start(self) -> None:
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('vim_tmux_pane', 0)
            yield variable_set_prefixed('tmux_socket', tmux_spec_socket)
        run().unsafe(self.vim)
        super()._pre_start()

    def vim_leave(self) -> Expectation:
        self._wait(.5)
        @do(NvimIO[List[Buffer]])
        def run() -> Do:
            yield nvim_command('MyoOpenPane', 'make')
            yield doautocmd('VimLeave')
        r = run().run_a(self.vim)
        self._wait(.5)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(1)))


__all__ = ('QuitSpec',)
