from kallikrein import Expectation, kf

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import pane

from ribosome.test.integration.klk import later

from unit._support.tmux import two_open_panes


class MinimizePaneSpec(TmuxSpec):
    '''
    minimize a tmux pane $minimize_pane
    '''

    def minimize_pane(self) -> Expectation:
        helper = two_open_panes().unsafe(self.tmux)
        helper.loop('command:minimize_pane', args=('one',)).unsafe(helper.vim)
        return later(kf(lambda: pane(0).unsafe(self.tmux).height) == 2)


__all__ = ('MinimizePaneSpec',)
