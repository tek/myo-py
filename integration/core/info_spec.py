from kallikrein import Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.length import have_length

from integration._support.spec import TmuxDefaultSpec

from chiasma.test.tmux_spec import tmux_spec_socket

from amino import List, do, Do

from ribosome.test.klk import kn
from ribosome.nvim.api.ui import current_buffer_content
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command


class InfoSpec(TmuxDefaultSpec):
    '''show information $info
    '''

    def _pre_start(self) -> None:
        @do(NvimIO[None])
        def run() -> Do:
            yield variable_set_prefixed('components', List('command', 'ui', 'tmux'))
            yield variable_set_prefixed('vim_tmux_pane', 0)
            yield variable_set_prefixed('tmux_socket', tmux_spec_socket)
            yield variable_set_prefixed('auto_jump', 0)
        run().unsafe(self.vim)
        super()._pre_start()

    def info(self) -> Expectation:
        @do(NvimIO[List[str]])
        def run() -> Do:
            yield nvim_command('MyoInfo')
            self._wait(1)
            yield current_buffer_content()
        return kn(self.vim, run).must(contain(have_length(10)))


__all__ = ('InfoSpec',)
