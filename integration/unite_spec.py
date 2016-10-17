from amino import List, __
from amino.test import later

from ribosome.test.unite import unite

from integration._support.command import CmdSpec


class UniteSpec(CmdSpec):

    @property
    def _plugins(self):
        return super()._plugins + List('myo.plugins.unite',
                                       'integration._support.plugins.dummy')

    @property
    def _cmd(self):
        return 'test1'

    @property
    def _history(self):
        return List(self._cmd, 'test2', 'test3')

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set('Myo_history', self._history.mk_string(','))

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name'))

    @unite
    def history(self, path):
        self.json_cmd_sync('MyoShellCommand {}'.format(self._cmd), line='ls')
        self.vim.cmd_sync('MyoUniteHistory')
        target = self._history / ' {}'.format
        later(lambda: self.vim.buffer.content.should.equal(target))
        self.vim.feedkeys('\r')
        later(lambda: self._last().should.contain(self._cmd))

__all__ = ('UniteSpec',)
