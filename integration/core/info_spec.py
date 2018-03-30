from kallikrein import Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.length import have_length

from integration._support.spec import DefaultSpec

from amino import List

from ribosome.nvim.api import current_buffer_content
from ribosome.test.klk import kn
from ribosome.test.integration.klk import later


class InfoSpec(DefaultSpec):
    '''run a test command $run
    '''

    def _pre_start(self) -> None:
        self.vim.vars.set_p('components', List('command', 'ui', 'tmux'))
        super()._pre_start()

    def run(self) -> Expectation:
        self.cmd_sync('MyoStage1')
        self.cmd_sync('MyoInfo')
        return later(kn(self.vim, current_buffer_content).must(contain(have_length(10))))


__all__ = ('InfoSpec',)
