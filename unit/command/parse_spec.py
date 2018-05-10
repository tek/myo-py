from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists, Nil, do, Do
from amino.test import fixture_path

from ribosome.config.config import Config
from ribosome.nvim.io.state import NS
from ribosome.test.config import TestConfig
from ribosome.test.unit import unit_test

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.env import Env
from myo.components.command.compute.parse import parse_output
from myo.config.plugin_state import MyoPluginState

from test.command import update_command_data

config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
)
test_config = TestConfig.cons(config)
trace_file = fixture_path('tmux', 'parse', 'trace')


@do(NS[MyoPluginState, Expectation])
def text_spec() -> Do:
    name = 'test'
    cmds = List('let g:key = 7', 'let g:value = 13')
    cmd = Command(name, VimInterpreter(silent=False, target=Nothing), cmds, Nil)
    yield update_command_data(commands=List(cmd))
    output = Lists.lines(trace_file.read_text())
    result = yield parse_output(output)
    return k(result.events).must(have_length(2))


class ParseSpec(SpecBase):
    '''
    parse text $text
    '''

    def text(self) -> Expectation:
        return unit_test(test_config, text_spec)


__all__ = ('ParseSpec',)
