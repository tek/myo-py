from amino.test import later
from amino import List, Path, Just
from amino.lazy import lazy

from ribosome.record import encode_json, decode_json

from myo.command import ShellCommand, Commands

from integration._support.command import CmdSpec


class _DispatchBase(CmdSpec):

    @property
    def _plugins(self):
        return super()._plugins.cat('integration._support.plugins.dummy')


class DispatchSpec(_DispatchBase):

    def autocmd(self):
        name = List.random_string(5)
        self.vim.autocmd('User', 'MyoRunCommand',
                         'let g:c = g:myo_last_command.name').run_sync()
        self._create_command(name, '')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(lambda: self.vim.vars('c').should.contain(name))

    def run_latest(self):
        name = 'test'
        self._create_command(name, '')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(lambda: self._last().should.contain(name))
        self.vim.vars.set_p('last_command', {})
        later(lambda: self._last().should.be.empty)
        self.vim.cmd_sync('MyoRunLatest')
        later(lambda: self._last().should.contain(name))

    def nonexistent(self):
        n = 'invalid'
        self._run_command(n)
        self._log_contains(Commands.no_such_command_error.format(n))

    def nonexistent_shell(self):
        n = 'invalid'
        self.json_cmd_sync('MyoRunInShell {}'.format(n))
        self._log_contains(Commands.no_such_shell_error.format(n))

    def no_history(self):
        self.json_cmd_sync('MyoRunLatest')
        self._log_contains(Commands.no_latest_command_error)


class HistorySpec(_DispatchBase):

    @lazy
    def _cmd(self):
        return List.random_string()

    def _set_vars(self):
        super()._set_vars()
        cmd = ShellCommand(name=self._cmd, line='',
                           log_path=Just(Path('/foo/bar')))
        history = encode_json([cmd]).get_or_raise
        self.vim.vars.set('Myo_history', history)

    def load_history(self):
        self._create_command(self._cmd, '')
        self.vim.cmd_sync('MyoRunLatest')
        later(lambda: self._last().should.contain(self._cmd))


class HistoryDistinctSpec(_DispatchBase):

    def history_distinct(self):
        name = 'name'
        test = lambda: self.json_cmd_sync(
            'MyoTest',
            ctor='py:integration.unite_spec._test_ctor'
        )
        self._create_command(name, 'ls')
        self._run_command(name)
        test()
        self._run_command(name)
        test()
        test()
        self._wait(1)
        hist = self.vim.vars('Myo_history') // decode_json | List()
        later(lambda: hist.should.have.length_of(2))

__all__ = ('DispatchSpec', 'HistorySpec')
