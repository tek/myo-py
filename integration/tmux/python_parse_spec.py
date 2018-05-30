from typing import Callable

from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers.length import have_length

from amino.test import fixture_path
from amino import List, Map, do, Do
from amino.test.spec import SpecBase

from ribosome.nvim.api.ui import current_buffer_content, send_input, buffers
from ribosome.nvim.io.compute import NvimIO
from ribosome.test.rpc import json_cmd
from ribosome.test.config import TestConfig
from ribosome.nvim.io.api import N
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.test.klk.expectation import await_k

from myo import myo_config

from integration._support.python_parse import events

vars = Map(
    myo_auto_jump=0,
)
test_config = TestConfig.cons(myo_config, vars=vars)


pane_ident = 'make'
file = fixture_path('tmux', 'python_parse', 'trace')
statements = List(
    'import pathlib',
    f'''print(pathlib.Path('{file}').read_text())''',
)

@do(NvimIO[Expectation])
def buffer_content() -> Do:
    lines = yield current_buffer_content()
    return k(lines).must(have_lines(events))


@do(NvimIO[Expectation])
def buffer_count_one() -> Do:
    bufs = yield buffers()
    return k(bufs).must(have_length(1))


@do(NvimIO[Expectation])
def parse_spec(run: Callable[[], NvimIO[None]]) -> Do:
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target=pane_ident, langs=List('python'))
    yield run()
    yield json_cmd('MyoParse')
    content = yield await_k(buffer_content)
    yield send_input('q')
    count = yield await_k(buffer_count_one)
    return content & count


@do(NvimIO[Expectation])
def line_spec() -> Do:
    yield parse_spec(lambda: json_cmd('MyoLine', shell='python', lines=statements, langs=List('python')))


@do(NvimIO[Expectation])
def command_spec() -> Do:
    @do(NvimIO[None])
    def run() -> Do:
        yield json_cmd('MyoAddShellCommand', ident='print', lines=statements, target='python')
        yield json_cmd('MyoRun', 'print')
    yield parse_spec(run)


class PythonParseSpec(SpecBase):
    '''
    parse a python traceback
    from line $line
    from command $command
    '''

    def line(self) -> Expectation:
        return tmux_plugin_test(test_config, line_spec)

    def command(self) -> Expectation:
        return tmux_plugin_test(test_config, command_spec)


__all__ = ('PythonParseSpec',)
