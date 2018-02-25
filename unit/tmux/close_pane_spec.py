from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO

from ribosome.test.integration.klk import later

from unit._support.tmux import two_open_panes


class ClosePaneSpec(TmuxSpec):
    '''
    close a tmux pane $close_pane
    '''

    def close_pane(self) -> Expectation:
        helper = two_open_panes().unsafe(self.tmux)
        helper.loop('command:close_pane', args=('one',)).unsafe(helper.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(1)))


__all__ = ('ClosePaneSpec',)
