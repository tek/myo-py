from amino import List, __, Just, _
from amino.test import later
from amino.lazy import lazy

from ribosome.test.unite import unite
from ribosome.record import encode_json

from myo.command import ShellCommand, CommandJob, TransientCommandJob
from myo.plugins.unite.format import unite_format, unite_format_str_command
from myo.plugins.command.main import CommandTransitions

from integration._support.command import CmdSpec

indent = ' {}'.format


class _UniteSpecBase(CmdSpec):

    @lazy
    def _name1(self):
        return 'com1'

    @lazy
    def _name2(self):
        return 'com2'

    @lazy
    def _cmd(self):
        return 'ls'

    def _create_commands(self):
        self._create_command(self._name1, self._cmd)
        self._create_command(self._name2, self._cmd)

    @property
    def _plugins(self):
        return super()._plugins + List('myo.plugins.unite',
                                       'integration._support.plugins.dummy')

    def _format(self, name, line):
        return indent(unite_format_str_command.format(name=name, line=line))


class UniteLoadHistorySpec(_UniteSpecBase):

    @property
    def _cmd(self):
        return 'test1'

    @lazy
    def _history(self):
        cmd = ShellCommand(name='other', line='ls')
        return List(
            CommandJob(command=ShellCommand(name=self._cmd, line='tee')),
            TransientCommandJob(command=cmd, override_line='tail')
        )

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set('Myo_history',
                          encode_json(self._history).get_or_raise)

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name'))

    @unite
    def history(self):
        self._create_command(self._cmd, 'ls')
        self.vim.cmd_sync('MyoUniteHistory')
        target = self._history / unite_format / _['word'] / indent
        later(lambda: self.vim.buffer.content.should.equal(target))


class UniteHistorySpec(_UniteSpecBase):

    @unite
    def history(self):
        self._create_commands()
        self._run_command(self._name1)
        self._run_command(self._name2)
        later(lambda: self._last().should.contain(self._name2))
        self.vim.cmd_sync('MyoUniteHistory')
        target = List(self._format(self._name2, self._cmd),
                      self._format(self._name1, self._cmd))
        later(lambda: self.vim.buffer.content.should.equal(target))
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('\r')
        later(lambda: self._last().should.contain(self._name2))
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
        target = unite_format_str_command.format(name='<test>',
                                                 line=_test_line)
        self._buffer_content(List(indent(target)))
        self.vim.feedkeys('\r')
        later(lambda: (self._last() | '').should.contain('test_line'))


class UniteCommandsSpec(_UniteSpecBase):

    def _pre_start(self):
        super()._pre_start()
        self.vim.vars.set_p(CommandTransitions._test_cmd_var, False)

    @unite
    def commands(self):
        self._create_commands()
        self.vim.cmd_sync('MyoUniteCommands')
        target = List(self._format(name=self._name1, line=self._cmd),
                      self._format(name=self._name2, line=self._cmd))
        later(lambda: self.vim.buffer.content.should.equal(target))
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('\r')
        later(lambda: self._last().should.contain(self._name2))
        self.vim.cmd_sync('MyoUniteCommands')
        later(lambda: self.vim.buffer.content.should.equal(target))

__all__ = ('UniteLoadHistorySpec', 'UniteHistorySpec', 'UniteCommandsSpec')
