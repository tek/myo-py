from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from chiasma.util.id import StrIdent

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists, do, Do
from amino.test import fixture_path

from ribosome.config.config import Config
from ribosome.nvim.io.state import NS
from ribosome.test.config import TestConfig
from ribosome.test.unit import unit_test
from ribosome.compute.ribosome_api import Ribo
from ribosome.compute.run import eval_prog

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter, CommandConfig
from myo.env import Env
from myo.components.command.compute.parse import parse_output
from myo.config.plugin_state import MyoState
from myo.components.command.data import CommandData

from test.command import update_command_data

name = StrIdent('test')
command_config = CommandConfig.cons(ident=name, parsers=List('unit._support.parsers.text'))
config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
)
test_config = TestConfig.cons(config)
trace_file = fixture_path('parse', 'trace', 'text')


@do(NS[MyoState, Expectation])
def text_spec() -> Do:
    cmds = List('let g:key = 7', 'let g:value = 13')
    cmd = Command.cons(name, VimInterpreter(silent=False, target=Nothing), cmds, config=name)
    yield update_command_data(commands=List(cmd), command_configs=List(command_config))
    output = Lists.lines(trace_file.read_text())
    result = yield eval_prog.match(Ribo.lift(parse_output(cmd, output, Nothing), CommandData))
    return k(result).must(have_length(2))


class ParseSpec(SpecBase):
    '''
    reference a command config $command_config
    '''

    def command_config(self) -> Expectation:
        return unit_test(test_config, text_spec)


__all__ = ('ParseSpec',)
