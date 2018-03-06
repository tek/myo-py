from typing import TypeVar

from ribosome.trans.api import trans
from ribosome.nvim.io import NS
from ribosome.config.config import Resources
from ribosome.dispatch.component import ComponentData

from chiasma.util.id import Ident

from amino import do, Do, List, Dat, __, Either, _, Maybe, IO, Lists, Just
from amino.lenses.lens import lens
from amino.boolean import true

from myo.settings import MyoSettings, setting
from myo.config.component import MyoComponent
from myo.env import Env
from myo.output import Parsing
from myo.output.data import ParseResult
from myo.components.command.data import CommandData
from myo.data.command import HistoryEntry
from myo.components.command.trans.output import display_parse_result
from myo.config.plugin_state import MyoPluginState

D = TypeVar('D')


class ParseConfig(Dat['ParseConfig']):

    def __init__(self, langs: List[str]) -> None:
        self.langs = langs


@do(NS[Resources[Env, MyoSettings, MyoComponent], None])
def parse_config() -> Do:
    yield NS.pure(ParseConfig(List('python')))


@do(NS[D, ParseResult])
def parse_output_with(output: List[str], config: ParseConfig) -> Do:
    parsing = yield NS.delay(lambda v: Parsing(v, config.langs))
    yield NS.from_io(parsing.parse(output, None))


@do(NS[Resources[ComponentData[Env, CommandData], MyoSettings, MyoComponent], ParseResult])
def parse_output(output: List[str]) -> Do:
    config = yield parse_config()
    yield parse_output_with(output, config)


@do(NS[CommandData, List[str]])
def cmd_output(ident: Ident) -> Do:
    log = yield NS.inspect_f(__.log_by_ident(ident))
    text = yield NS.from_io(IO.delay(log.read_text))
    return Lists.lines(text)


def most_recent_command() -> NS[CommandData, Either[str, HistoryEntry]]:
    return NS.inspect(lambda s: s.history.head.to_either(f'history is empty') / _.cmd)


class ParseOptions(Dat['ParseOptions']):

    def __init__(self, pane: Maybe[Ident], command: Maybe[Ident], langs: List[str]) -> None:
        self.pane = pane
        self.command = command
        self.langs = langs


@do(NS[CommandData, List[str]])
def fetch_output() -> Do:
    cmd_e = yield most_recent_command()
    cmd = yield NS.from_either(cmd_e)
    yield cmd_output(cmd.ident)


@do(NS[Resources[ComponentData[Env, CommandData], MyoSettings, MyoComponent], None])
def parse_most_recent() -> Do:
    output = yield fetch_output().zoom(lens.data.comp)
    yield parse_output(output)


@trans.free.unit(trans.st, internal=true)
@do(NS[Resources[ComponentData[MyoPluginState, CommandData], MyoSettings, MyoComponent], None])
def parse() -> Do:
    parse_result = yield parse_most_recent()
    yield NS.modify(__.set.parse_result(Just(parse_result))).zoom(lens.data.comp)
    display_result = yield setting(_.display_parse_result)
    yield display_parse_result(parse_result).zoom(lens.data) if display_result else NS.unit


__all__ = ('parse',)
