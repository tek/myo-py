from kallikrein import Expectation, k
from kallikrein.matchers.end_with import end_with

from amino import do, Do, List, Lists, Nil
from amino.test import fixture_path
from amino.test.spec import SpecBase

from ribosome.compute.run import run_prog
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.io.state import NS

from myo.components.command.compute.test import vim_test, vim_test_command, test_ident
from myo.components.command.compute.run import RunCommandOptions
from myo.config.plugin_state import MyoPluginState

from test.command import command_spec_test_config
from test.test import mock_test_functions


file = fixture_path('command', 'test', 'code.py')
target = List('  File "<string>", line 1, in <module>', 'RuntimeError: No active exception to reraise')


@do(NS[MyoPluginState, Expectation])
def create_cmd_spec() -> Do:
    yield NS.lift(mock_test_functions())
    yield run_prog(vim_test_command, Nil)
    cmd = yield NS.inspect_either(lambda s: s.data_by_name('command'))
    comp = yield NS.e(cmd.commands.head.to_either('no commands'))
    return k(comp.ident) == test_ident


@do(NS[MyoPluginState, Expectation])
def run_spec() -> Do:
    yield NS.lift(mock_test_functions())
    yield run_prog(vim_test, List(RunCommandOptions.cons()))
    cmd = yield NS.inspect_either(lambda s: s.data_by_name('command'))
    log = yield NS.e(cmd.log_by_ident(test_ident))
    return k(Lists.lines(log.read_text())).must(end_with(target))


class TestSpec(SpecBase):
    '''
    create the test command if it doesn't exist $create_cmd
    run a test comand $run
    '''

    def create_cmd(self) -> Expectation:
        return external_state_test(command_spec_test_config, create_cmd_spec)

    def run(self) -> Expectation:
        return external_state_test(command_spec_test_config, run_spec)


__all__ = ('TestSpec',)
