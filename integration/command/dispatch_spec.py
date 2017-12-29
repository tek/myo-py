from amino import List, Path, Just, Map, __
from amino.lazy import lazy

from kallikrein import k, Expectation, kf
from kallikrein.matchers import contain
from kallikrein.matchers.maybe import be_nothing
from kallikrein.matchers.length import have_length

from ribosome.test.integration.klk import later

from myo.command import ShellCommand, Commands
from myo.components.command.message import AddShellCommand, RunChained

from integration._support.command import CmdSpec, CmdSpecConf
from integration._support.base import MyoIntegrationSpec


class _DispatchBase(CmdSpec):

    @property
    def _plugins(self) -> List[str]:
        return super()._plugins.cat('integration._support.components.dummy')


def _chain(cmds: List[str]) -> str:
    return ' && '.join(cmds)


class DispatchSpec(_DispatchBase):
    '''command dispatching
    the autocmd `MyoRunCommand` gets triggered $autocmd
    the variable `myo_last_command` contains the name of the most recently run command $run_latest
    specifying a nonexistent command name logs an error $nonexistent
    specifying a nonexistent shell name logs an error $nonexistent_shell
    executing `MyoRunLatest` when the history is empty logs an error $no_history
    '''

    def autocmd(self) -> Expectation:
        name = List.random_string(5)
        self.vim.autocmd('User', 'MyoRunCommand', 'let g:c = g:myo_last_command.name').run_sync()
        self._create_command(name, '')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        return later(kf(self.vim.vars, 'c').must(contain(name)))

    def run_latest(self) -> Expectation:
        name = 'test'
        self._create_command(name, '')
        self.vim.cmd_sync('MyoRun {}'.format(name))
        later(kf(self._last).must(contain(name)))
        self.vim.vars.set_p('last_command', {})
        later(kf(self._last).must(be_nothing))
        self.vim.cmd_sync('MyoRunLatest')
        return later(kf(self._last).must(contain(name)))

    def nonexistent(self) -> Expectation:
        n = 'invalid'
        self._run_command(n)
        return self._log_contains(Commands.no_such_command_error.format(n))

    def nonexistent_shell(self) -> Expectation:
        n = 'invalid'
        self.json_cmd_sync('MyoRunInShell {}'.format(n))
        return self._log_contains(Commands.no_such_shell_error.format(n))

    def no_history(self) -> Expectation:
        self.json_cmd_sync('MyoRunLatest')
        return self._log_contains(Commands.no_latest_command_error)


class ChainSpec(CmdSpecConf, MyoIntegrationSpec):
    '''chain two commands using a python callback and run them $run_chained
    '''

    @property
    def _plugins(self) -> List[str]:
        return super()._plugins.cat('integration._support.components.dummy')

    def run_chained(self) -> Expectation:
        self.vim.vars.set_p('chainer', 'py:integration.command.dispatch_spec._chain')
        from myo.components.command.main import CommandTransitions
        name1 = 'test1'
        name2 = 'test2'
        line = 'print \'{}\''
        text1 = List.random_string()
        text2 = List.random_string()
        text3 = List.random_string()
        line1 = line.format(text1)
        line2 = line.format(text2)
        line3 = line.format(text3)
        (
            flexmock(CommandTransitions)
            .should_receive('_vim_test_line')
            .and_return(Just(line3))
        )
        chained = _chain(List(line1, line2, line3))
        self.root.send_sync(AddShellCommand(name1, Map(line=line1)))
        self.root.send_sync(AddShellCommand(name2, Map(line=line2)))
        self.root.send_sync(RunChained(name1, name2, 's:vimtest'))
        line = self.root.data.commands.history.last // __.line.resolve(None)
        return k(line).must(contain(chained))


class HistorySpec(_DispatchBase):
    '''history
    the history state file is read at startup to populate the history $load_history
    '''

    @lazy
    def cmd_name(self):
        return List.random_string()

    def _set_vars(self):
        super()._set_vars()
        cmd = ShellCommand(name=self.cmd_name, line='', log_path=Just(Path('/foo/bar')))
        self.write_history(List(cmd))

    def load_history(self) -> Expectation:
        self._create_command(self.cmd_name, '')
        self.vim.cmd_sync('MyoRunLatest')
        return later(kf(self._last).must(contain(self.cmd_name)))


class HistoryDistinctSpec(_DispatchBase):
    '''distinct history entries
    earlier entries of the same command are deleted on reexecution $history_distinct
    '''

    def history_distinct(self) -> Expectation:
        name = 'name'
        def test() -> None:
            self.json_cmd_sync('MyoTest', ctor='py:integration.unite_spec._test_ctor')
        self._create_command(name, 'ls')
        self._run_command(name)
        test()
        self._run_command(name)
        test()
        test()
        return later(kf(self.history).must(have_length(2)))

__all__ = ('DispatchSpec', 'HistorySpec', 'HistoryDistinctSpec', 'ChainSpec')
