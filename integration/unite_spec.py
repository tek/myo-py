from amino import List, __, Just, _
from amino.test import later
from amino.lazy import lazy

from ribosome.test.unite import unite
from ribosome.record import encode_json

from myo.command import ShellCommand, Command, TransientCommand
from myo.plugins.unite.format import unite_format

from integration._support.command import CmdSpec


class _UniteSpecBase(CmdSpec):

    @property
    def _plugins(self):
        return super()._plugins + List('myo.plugins.unite',
                                       'integration._support.plugins.dummy')


class UniteLoadHistorySpec(_UniteSpecBase):

    @property
    def _cmd(self):
        return 'test1'

    @lazy
    def _history(self):
        cmd = ShellCommand(name='other', line='ls')
        return List(Command(name=self._cmd),
                    TransientCommand(command=cmd, line='tail'))

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set('Myo_history',
                          encode_json(self._history).get_or_raise)

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name'))

    @unite
    def history(self):
        indent = ' {}'.format
        self._create_command(self._cmd, 'ls')
        self.vim.cmd_sync('MyoUniteHistory')
        target = self._history / unite_format / _['word'] / indent
        later(lambda: self.vim.buffer.content.should.equal(target))


class UniteHistorySpec(_UniteSpecBase):

    @unite
    def history(self):
        name1 = 'com1'
        name2 = 'com2'
        cmd = 'ls'
        self._create_command(name1, cmd)
        self._create_command(name2, cmd)
        self._run_command(name1)
        self._run_command(name2)
        form = ' {}'.format
        later(lambda: self._last().should.contain(name2))
        self.vim.cmd_sync('MyoUniteHistory')
        target = List(form(name2), form(name1))
        later(lambda: self.vim.buffer.content.should.equal(target))
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('\r')
        later(lambda: self._last().should.contain(name2))
        self.vim.cmd_sync('MyoUniteHistory')
        later(lambda: self.vim.buffer.content.should.equal(target.reversed))

_test_line = 'echo \'testing\''


def _test_ctor():
    return Just(_test_line)


class UniteTestSpec(_UniteSpecBase):

    @unite
    def unite_test_run(self):
        self.json_cmd_sync('MyoTest',
                           ctor='py:integration.unite_spec._test_ctor')
        later(lambda: (self._last() | '').should.contain('test_line'))
        self.vim.vars.set_p('last_command', {})
        self.vim.cmd_sync('MyoUniteHistory')
        self._wait(1)
        self._buffer_content(List(' <test> {}'.format(_test_line)))
        self.vim.feedkeys('\r')
        later(lambda: (self._last() | '').should.contain('test_line'))

__all__ = ('UniteLoadHistorySpec', 'UniteHistorySpec')
