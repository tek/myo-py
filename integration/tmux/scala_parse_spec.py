from kallikrein import Expectation
from kallikrein.matchers import contain

from amino.test import fixture_path
from amino import List, Map, do, Do, Lists, IO
from amino.test.spec import SpecBase

from ribosome.nvim.api.ui import send_input
from ribosome.nvim.io.compute import NvimIO
from ribosome.test.rpc import json_cmd
from ribosome.nvim.io.api import N
from ribosome.test.integration.tmux import tmux_plugin_test
from ribosome.test.klk.matchers.buffer import current_buffer_contains, buffer_count_is

from myo import myo_config

from test.klk.tmux import pane_content_matches
from test.tmux import tmux_test_config

from integration._support.scala_parse import events

vars = Map(
    myo_auto_jump=0,
)
test_config = tmux_test_config(config=myo_config, extra_vars=vars)


pane_ident = 'make'
file = fixture_path('tmux', 'scala_parse', 'errors')
statements = List(
    'import pathlib',
    f'''print(pathlib.Path('{file}').read_text())''',
)


@do(NvimIO[Expectation])
def parse_spec() -> Do:
    file_content = yield N.from_io(IO.delay(Lists.file, file))
    line = yield N.from_maybe(file_content.head, f'no content in fixture')
    yield json_cmd('MyoAddSystemCommand', ident='python', line='python', target=pane_ident)
    yield json_cmd('MyoLine', shell='python', lines=statements, langs=List('scala'))
    executed = yield pane_content_matches(contain(line), 1, timeout=10)
    yield json_cmd('MyoParse')
    content = yield current_buffer_contains(Lists.lines(events).drop_right(1))
    yield send_input('q')
    bufs = yield buffer_count_is(1)
    return executed & content & bufs


class ScalaParseSpec(SpecBase):
    '''
    parse scala compiler errors $parse
    '''

    def parse(self) -> Expectation:
        return tmux_plugin_test(test_config, parse_spec)


__all__ = ('ScalaParseSpec',)
