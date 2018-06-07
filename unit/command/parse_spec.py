from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from chiasma.util.id import StrIdent

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists, do, Do, Nil
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
from myo.config.plugin_state import MyoState
from myo.components.command.data import CommandData
from myo.output.data.output import OutputEvent
from myo.components.command.parse import parse_output
from myo.components.command.compute.tpe import CommandRibosome

from test.command import update_command_data

from unit._support.parsers.text import TextLine

name = StrIdent('test')
config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
)
test_config = TestConfig.cons(config)
trace_file = fixture_path('parse', 'trace', 'text')
parsers = List('unit._support.parsers.text')


@do(NS[MyoState, List[OutputEvent[TextLine]]])
def run_parser(command_config: CommandConfig) -> Do:
    cmd = Command.cons(name, VimInterpreter.default(), Nil, config=name)
    yield update_command_data(commands=List(cmd), command_configs=List(command_config))
    output = Lists.lines(trace_file.read_text())
    yield eval_prog.match(Ribo.lift(parse_output(cmd, output, Nothing), CommandData))


@do(NS[MyoState, Expectation])
def text_spec() -> Do:
    command_config = CommandConfig.cons(ident=name, parsers=parsers)
    result = yield run_parser(command_config)
    return k(result).must(have_length(2))


def filter_output(events: List[OutputEvent]) -> NS[CommandRibosome, List[OutputEvent]]:
    return NS.pure(events.take(1))


@do(NS[MyoState, Expectation])
def output_filter_spec() -> Do:
    command_config = CommandConfig.cons(ident=name, parsers=parsers,
                                        output_filter=List('unit.command.parse_spec.filter_output'))
    result = yield run_parser(command_config)
    return k(result).must(have_length(1))


class ParseSpec(SpecBase):
    '''
    reference a command config $command_config
    custom output filter $output_filter
    '''

    def command_config(self) -> Expectation:
        return unit_test(test_config, text_spec)

    def output_filter(self) -> Expectation:
        return unit_test(test_config, output_filter_spec)


__all__ = ('ParseSpec',)
