from time import sleep
import json

from integration._support.base import VimIntegrationSpec

from tryp import List


class Command_(VimIntegrationSpec):

    @property
    def _plugins(self):
        return List('myo.plugins.command')

    def setup(self):
        super().setup()

    def _json(self, **params):
        return json.dumps(params).replace('"', '\\"')

    def test(self):
        from myo.logging import print_info
        print_info(print)
        self._debug = True
        sleep(1)
        params = self._json(line='ls', name='ls')
        self.vim.cmd_sync('MyoVimCommand tc {}'.format(params))
        sleep(1)

__all__ = ('Command_',)
