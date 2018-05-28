from typing import TypeVar

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import Ident, IdentSpec

from amino import do, Do, List, Dat, __, _, Maybe, IO, Lists, Just
from amino.logging import module_log

from myo.output.data.output import ParseResult
from myo.components.command.data import CommandData
from myo.data.command import HistoryEntry, Command
from myo.components.command.compute.output import render_parse_result
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import display_parse_result
from myo.output.main import parse_with_langs

log = module_log()
D = TypeVar('D')


class ParseConfig(Dat['ParseConfig']):

    def __init__(self, langs: List[str]) -> None:
        self.langs = langs


@do(NS[CommandRibosome, None])
def parse_config(cmd: Command) -> Do:
    yield NS.pure(ParseConfig(cmd.langs))


@do(NS[D, ParseResult])
def parse_output_with(output: List[str], config: ParseConfig) -> Do:
    yield NS.e(parse_with_langs(output, config.langs))


@do(NS[CommandRibosome, ParseResult])
def parse_output(cmd: Command, output: List[str]) -> Do:
    config = yield parse_config(cmd)
    yield parse_output_with(output, config)


@do(NS[CommandData, List[str]])
def cmd_output(ident: Ident) -> Do:
    log = yield NS.inspect_either(__.log_by_ident(ident))
    text = yield NS.from_io(IO.delay(log.read_text))
    return Lists.lines(text)


def most_recent_command() -> NS[CommandData, HistoryEntry]:
    return NS.inspect_either(lambda s: s.history.last.to_either(f'history is empty') / _.cmd)


class ParseOptions(Dat['ParseOptions']):

    @staticmethod
    def cons(pane: IdentSpec=None, command: IdentSpec=None, langs: List[str]=None) -> 'ParseOptions':
        return ParseOptions(Maybe.optional(pane), Maybe.optional(command), Maybe.optional(langs))

    def __init__(self, pane: Maybe[Ident], command: Maybe[Ident], langs: Maybe[List[str]]) -> None:
        self.pane = pane
        self.command = command
        self.langs = langs


@do(NS[CommandRibosome, None])
def parse_command(cmd: Command) -> Do:
    output = yield Ribo.zoom_comp(cmd_output(cmd.ident))
    yield parse_output(cmd, output)


@do(NS[CommandRibosome, None])
def parse_most_recent() -> Do:
    cmd = yield Ribo.zoom_comp(most_recent_command())
    yield parse_command(cmd)


@prog.unit
@do(NS[CommandRibosome, None])
def parse(options: ParseOptions) -> Do:
    parse_result = yield parse_most_recent()
    yield Ribo.modify_comp(__.set.parse_result(Just(parse_result)))
    display_result = yield Ribo.setting(display_parse_result)
    yield render_parse_result(parse_result) if display_result else NS.unit


__all__ = ('parse',)
