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
def parse_spec() -> Do:
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target=pane_ident)
    yield json_cmd('MyoLine', shell='python', lines=statements, langs=List('python'))
    yield json_cmd('MyoParse')
    yield N.sleep(1)
    lines = yield current_buffer_content()
    yield send_input('q')
    yield N.sleep(1)
    bufs = yield buffers()
    return k(lines).must(have_lines(events)) & k(bufs).must(have_length(1))


class PythonParseSpec(SpecBase):
    '''
    parse a python traceback $parse
    '''

    def parse(self) -> Expectation:
        return tmux_plugin_test(test_config, parse_spec)


__all__ = ('PythonParseSpec',)
