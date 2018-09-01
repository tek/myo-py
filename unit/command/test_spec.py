from kallikrein import Expectation, k
from kallikrein.matchers.end_with import end_with

from amino import do, Do, List, Lists, Map
from amino.test import fixture_path
from amino.test.spec import SpecBase

from ribosome.compute.run import run_prog
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.io.state import NS
from ribosome.test.config import TestConfig

from myo.components.command.compute.test import vim_test, vim_test_command, test_ident
from myo.components.command.compute.run import RunCommandOptions
from myo.config.plugin_state import MyoState
from myo import myo_config

from test.command import command_spec_test_config
from test.test import mock_test_functions

test_config = TestConfig.cons(myo_config, components=List('command', 'ui'), vars=Map(myo_test_ui='internal'))
file = fixture_path('command', 'test', 'code.py')
target = List('  File "<string>", line 1, in <module>', 'RuntimeError: No active exception to reraise')


@do(NS[MyoState, Expectation])
def create_cmd_spec() -> Do:
    yield NS.lift(mock_test_functions())
    yield run_prog(vim_test_command, List(List('python')))
    cmd = yield NS.inspect_either(lambda s: s.data_by_name('command'))
    comp = yield NS.e(cmd.commands.head.to_either('no commands'))
    return k(comp.ident) == test_ident


@do(NS[MyoState, Expectation])
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
        return external_state_test(test_config, run_spec)


__all__ = ('TestSpec',)
