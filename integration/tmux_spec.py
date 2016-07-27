from tryp import List, _
from tryp.test import later

from integration._support.base import TmuxIntegrationSpec


class TmuxSpec(TmuxIntegrationSpec):

    @property
    def _plugins(self):
        return List('myo.plugins.tmux')

    def open_pane(self):
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            panes.should.have.length_of(2)
        self._debug = True
        self.json_cmd('MyoTmuxCreatePane', name='pan', layout='vim',
                      min_size=0.5, weight=0.1)
        self.json_cmd('MyoTmuxOpenPane pan', layout='vim')
        later(check)
        self.vim.cmd('MyoTmuxTest')
        self._wait(1)

__all__ = ('TmuxSpec',)
