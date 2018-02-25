from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO

from ribosome.test.integration.klk import later

from unit._support.tmux import two_panes


class OpenPaneSpec(TmuxSpec):
    '''
    open a tmux pane $open_pane
    '''

    def open_pane(self) -> Expectation:
        helper = two_panes()
        state = helper.loop('command:open_pane', args=('one', '{}')).unsafe(helper.vim)
        helper1 = helper.set.state(state)
        helper1.loop('command:open_pane', args=('two', '{}')).unsafe(helper.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(2)))


__all__ = ('OpenPaneSpec',)
