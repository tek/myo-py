from tryp import List

from integration._support.base import TmuxIntegrationSpec


class TmuxSpec(TmuxIntegrationSpec):

    @property
    def _plugins(self):
        return List('myo.plugins.tmux')

    def startup(self):
        self._debug = True
        self.json_cmd('MyoTmuxCreatePane', name='pan', layout='vim')
        self.json_cmd('MyoTmuxOpenPane pan', layout='vim')
        self._wait(3)

__all__ = ('TmuxSpec',)
