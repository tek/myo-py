from kallikrein import kf, Expectation, k
from kallikrein.matchers import contain
from kallikrein.matchers.either import be_right

from amino.lazy import lazy
from amino import List, __, Just, Maybe, _, Lists

from ribosome.test.unite import unite
from ribosome.record import encode_json
from ribosome.test.integration.klk import later

from myo.command import ShellCommand, CommandJob, TransientCommandJob
from myo.components.unite.format import unite_format, unite_format_str_command
from myo.components.command.main import CommandComponent
from myo.components.unite.data import UniteNames

from integration._support.command import CmdSpec

indent = ' {}'.format


class _UniteSpecBase(CmdSpec):

    @lazy
    def _name1(self) -> str:
        return 'com1'

    @lazy
    def _name2(self) -> str:
        return 'com2'

    @lazy
    def _command(self) -> str:
        return 'ls'

    def _create_commands(self) -> None:
        self._create_command(self._name1, self._command)
        self._create_command(self._name2, self._command)

    @property
    def _plugins(self) -> List[str]:
        return super()._plugins + List('unite', 'integration._support.components.dummy')

    def _format(self, name: str, line: str) -> str:
        return indent(unite_format_str_command.format(name=name, line=line))


class UniteLoadHistorySpec(_UniteSpecBase):
    '''show the command history in a unite window $history
    '''

    @property
    def _command(self) -> str:
        return 'test1'

    @lazy
    def _history(self) -> List[CommandJob]:
        cmd = ShellCommand(name='other', line='ls')
        return List(
            CommandJob(command=ShellCommand(name=self._command, line='tee')),
            TransientCommandJob(command=cmd, override_line='tail')
        )

    def _set_vars(self) -> None:
        super()._set_vars()
        self.vim.vars.set('Myo_history', encode_json(self._history).get_or_raise)

    @unite
    def history(self) -> Expectation:
        self._create_command(self._command, 'ls')
        self.vim.cmd_sync('MyoUniteHistory')
        target = self._history / unite_format / (lambda a: a['word']) / indent
        return self._buffer_content(target)


class UniteHistoryRunSpec(_UniteSpecBase):
    ''' interact with history commands from unite
    run a command $run
    delete a history entry $delete
    '''

    @property
    def target(self) -> List[str]:
        return List(self._format(self._name2, self._command),
                    self._format(self._name1, self._command))

    @unite
    def run(self) -> Expectation:
        '''Not that the unite window is aligned top and the latest history entry is in line 1
        '''
        self._create_commands()
        self._run_command(self._name1)
        self._run_command(self._name2)
        later(kf(self._last).must(be_right(self._name2)))
        self.vim.cmd_sync('MyoUniteHistory')
        self._buffer_content(self.target)
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('\r')
        later(kf(self._last).must(be_right(self._name1)))
        self.vim.cmd_sync('MyoUniteHistory')
        return self._buffer_content(self.target.reversed)

    @unite
    def delete(self) -> Expectation:
        self._create_commands()
        self._run_command(self._name1)
        self._run_command(self._name2)
        later(kf(self._last).must(be_right(self._name2)))
        self.vim.cmd_sync('MyoUniteHistory')
        self._buffer_content(self.target)
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('d')
        self._wait(2)
        self.vim.cmd_sync('MyoUniteHistory')
        self._wait(1)
        return self._buffer_content(self.target[:1])

_test_line = 'echo \'testing\''


def _test_ctor() -> Maybe[str]:
    return Just(_test_line)


class UniteTestSpec(_UniteSpecBase):
    '''test command formatting in the history $unite_test_history
    '''

    @unite
    def unite_test_history(self) -> Expectation:
        def check() -> Expectation:
            return later(kf(self._last).must(contain(contain('test_line'))))
        self.json_cmd_sync('MyoTest', ctor='py:integration.unite_spec._test_ctor')
        check()
        self.vim.vars.set_p('last_command', {})
        self.vim.cmd_sync('MyoUniteHistory')
        target = unite_format_str_command.format(name='<test>', line=_test_line)
        self._buffer_content(List(indent(target)))
        self.vim.feedkeys('\r')
        return check()


cc_name = UniteNames.commands_candidates


class UniteCommandsSpec(_UniteSpecBase):
    f'''return all commands from `{cc_name}` $candidates
    show all commands in the unite window $commands
    '''

    def _pre_start(self) -> None:
        self.vim.vars.set_p(CommandComponent._test_cmd_var, False)
        super()._pre_start()

    @property
    def target(self) -> List[str]:
        return List(self._format(name=self._name1, line=self._command),
                    self._format(name=self._name2, line=self._command))

    def candidates(self) -> Expectation:
        self._create_commands()
        c = self.vim.call(cc_name).map(Lists.wrap).map(__.map(_['word']).map(lambda a: f' {a}'))
        return k(c).must(be_right(self.target))

    @unite
    def commands(self) -> Expectation:
        self._create_commands()
        self.vim.cmd_sync('MyoUniteCommands')
        self._buffer_content(self.target)
        self.vim.window.set_cursor(2)
        self.vim.feedkeys('\r')
        later(kf(self._last).must(contain(self._name2)))
        self.vim.cmd_sync('MyoUniteCommands')
        return self._buffer_content(self.target)

__all__ = ('UniteLoadHistorySpec', 'UniteHistoryRunSpec', 'UniteCommandsSpec', 'UniteTestSpec')
