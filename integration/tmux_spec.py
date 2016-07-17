from tryp import List, _

from integration._support.base import TmuxIntegrationSpec


class TmuxSpec(TmuxIntegrationSpec):

    @property
    def _plugins(self):
        return List('myo.plugins.tmux')

    def open_pane(self):
        self._debug = True
        self.json_cmd('MyoTmuxCreatePane', name='pan', layout='vim')
        self.json_cmd('MyoTmuxOpenPane pan', layout='vim')
        self._wait(1)
        print(self.server.sessions.head // _.windows.head / _.panes)
        self.vim.cmd('MyoTmuxTest')
        self._wait(1)

__all__ = ('TmuxSpec',)
