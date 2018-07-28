from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import contain

from amino import do, Do, List, Map
from amino.test import fixture_path
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N
from ribosome.nvim.api.ui import buffers, buffer_content
from ribosome.test.rpc import json_cmd
from ribosome.test.integration.embed import plugin_test
from ribosome.nvim.api.data import Buffer
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.api.util import nvimio_await_success
from ribosome.test.config import TestConfig
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.nvim.api.function import define_function

from myo import myo_config
from myo.settings import test_shell
from myo.tmux.io import tmux_to_nvim

from test.test import mock_test_functions
from test.tmux import tmux_test_config
from test.klk.tmux import pane_content_matches

from chiasma.commands.pane import all_panes


test_config = TestConfig.cons(myo_config, vars=Map(myo_test_ui='internal'))
file = fixture_path('command', 'test', 'code.py')
target = List('<string>  1 <module>', 'RuntimeError: No active exception to reraise')


@do(NvimIO[Buffer])
def scratch_buffer() -> Do:
    bufs = yield buffers()
    yield N.from_maybe(bufs.lift(1), 'scratch buffer wasn\'t opened')


@do(NvimIO[Buffer])
def scratch_content() -> Do:
    buf = yield nvimio_await_success(scratch_buffer, 1.)
    content = yield buffer_content(buf)
    return k(content).must(have_lines(target))


@do(NvimIO[Expectation])
def parse_spec() -> Do:
    yield mock_test_functions()
    yield json_cmd('MyoVimTest', langs=['python'])
    yield json_cmd('MyoParse')
    yield await_k(scratch_content)


@do(NvimIO[None])
def mock_shell_test_functions() -> Do:
    yield define_function('MyoTestDetermineRunner', List('file'), f'return "python"')
    yield define_function('MyoTestExecutable', List('runner'), f'return "print"')
    yield define_function('MyoTestBuildPosition', List('runner', 'pos'), f'return ["(\'value\')"]')
    yield define_function('MyoTestBuildArgs', List('runner', 'args'), f'return a:args')


@do(NvimIO[Expectation])
def shell_spec() -> Do:
    yield mock_shell_test_functions()
    yield test_shell.update('python')
    yield json_cmd('MyoCreatePane', layout='make', ident='python')
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target='python', langs=List('python'))
    yield json_cmd('MyoVimTest', langs=List('python'))
    yield pane_content_matches(contain('value'), 2, timeout=5)


# TODO test empty `ParseOutput`
class TestSpec(SpecBase):
    '''run and parse a python test command $parse
    run a python test command in a shell $shell
    '''

    def parse(self) -> Expectation:
        return plugin_test(test_config, parse_spec)

    def shell(self) -> Expectation:
        test_config = tmux_test_config(myo_config)
        return tmux_plugin_test(test_config, shell_spec)


__all__ = ('TestSpec',)
