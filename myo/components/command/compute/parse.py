from typing import TypeVar

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.config.resources import Resources
from ribosome.config.component import ComponentData
from ribosome.util.setting import setting
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import Ident, IdentSpec

from amino import do, Do, List, Dat, __, Either, _, Maybe, IO, Lists, Just
from amino.lenses.lens import lens

from myo.settings import MyoSettings
from myo.output import Parsing
from myo.output.data import ParseResult
from myo.components.command.data import CommandData
from myo.data.command import HistoryEntry
from myo.components.command.compute.output import display_parse_result
from myo.components.command.compute.tpe import CommandRibosome

D = TypeVar('D')


class ParseConfig(Dat['ParseConfig']):

    def __init__(self, langs: List[str]) -> None:
        self.langs = langs


@do(NS[CommandRibosome, None])
def parse_config() -> Do:
    yield NS.pure(ParseConfig(List('python')))


@do(NS[D, ParseResult])
def parse_output_with(output: List[str], config: ParseConfig) -> Do:
    parsing = yield NS.delay(lambda v: Parsing(v, config.langs))
    yield NS.from_io(parsing.parse(output, None))


@do(NS[CommandRibosome, ParseResult])
def parse_output(output: List[str]) -> Do:
    config = yield parse_config()
    yield parse_output_with(output, config)


@do(NS[CommandData, List[str]])
def cmd_output(ident: Ident) -> Do:
    log = yield NS.inspect_either(__.log_by_ident(ident))
    text = yield NS.from_io(IO.delay(log.read_text))
    return Lists.lines(text)


def most_recent_command() -> NS[CommandData, Either[str, HistoryEntry]]:
    return NS.inspect(lambda s: s.history.last.to_either(f'history is empty') / _.cmd)


class ParseOptions(Dat['ParseOptions']):

    @staticmethod
    def cons(pane: IdentSpec=None, command: IdentSpec=None, langs: List[str]=None) -> 'ParseOptions':
        return ParseOptions(Maybe.optional(pane), Maybe.optional(command), Maybe.optional(langs))

    def __init__(self, pane: Maybe[Ident], command: Maybe[Ident], langs: Maybe[List[str]]) -> None:
        self.pane = pane
        self.command = command
        self.langs = langs


@do(NS[CommandData, List[str]])
def fetch_output() -> Do:
    cmd_e = yield most_recent_command()
    cmd = yield NS.from_either(cmd_e)
    yield cmd_output(cmd.ident)


@do(NS[CommandRibosome, None])
def parse_most_recent() -> Do:
    output = yield Ribo.zoom_comp(fetch_output())
    yield parse_output(output)


@prog.unit
@do(NS[CommandRibosome, None])
def parse(options: ParseOptions) -> Do:
    parse_result = yield parse_most_recent()
    yield Ribo.modify_comp(__.set.parse_result(Just(parse_result)))
    display_result = yield Ribo.setting(_.display_parse_result)
    yield display_parse_result(parse_result) if display_result else NS.unit


__all__ = ('parse',)
