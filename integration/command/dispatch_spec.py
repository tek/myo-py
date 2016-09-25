from integration._support.command import CmdSpec

from amino.test import later
from amino import __, List


class _DispatchBase(CmdSpec):

    @property
    def _plugins(self):
        return super()._plugins.cat('integration._support.plugins.dummy')

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name'))


class DispatchSpec(_DispatchBase):

    def autocmd(self):
        name = List.random_string(5)
        self.vim.autocmd('User', 'MyoRunCommand',
                         'let g:c = g:myo_last_command.name').run_sync()
        self.json_cmd('MyoShellCommand {}'.format(name), line='')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(lambda: self.vim.vars('c').should.contain(name))

    def run_latest(self):
        name = 'test'
        self.json_cmd('MyoShellCommand {}'.format(name), line='')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(lambda: self._last().should.contain(name))
        self.vim.vars.set_p('last_command', {})
        later(lambda: self._last().should.be.empty)
        self.vim.cmd_sync('MyoRunLatest')
        later(lambda: self._last().should.contain(name))


class HistorySpec(_DispatchBase):

    @property
    def _cmd(self):
        return 'test'

    def _set_vars(self):
        super()._set_vars()
        history = self._cmd
        self.vim.vars.set('Myo_history', history)

    def load_history(self):
        self.json_cmd_sync('MyoShellCommand {}'.format(self._cmd), line='')
        self.vim.cmd_sync('MyoRunLatest')
        later(lambda: self._last().should.contain(self._cmd))

__all__ = ('DispatchSpec', 'HistorySpec')
