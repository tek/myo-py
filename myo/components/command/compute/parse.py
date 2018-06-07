from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from chiasma.util.id import IdentSpec, Ident

from amino import do, Do, Just, Dat, Maybe, List
from amino.logging import module_log

from myo.components.command.compute.output import render_parse_result
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import display_parse_result
from myo.components.command.parse import parse_most_recent

log = module_log()


class ParseOptions(Dat['ParseOptions']):

    @staticmethod
    def cons(pane: IdentSpec=None, command: IdentSpec=None, langs: List[str]=None) -> 'ParseOptions':
        return ParseOptions(Maybe.optional(pane), Maybe.optional(command), Maybe.optional(langs))

    def __init__(self, pane: Maybe[Ident], command: Maybe[Ident], langs: Maybe[List[str]]) -> None:
        self.pane = pane
        self.command = command
        self.langs = langs


@prog.unit
@do(NS[CommandRibosome, None])
def parse(options: ParseOptions) -> Do:
    parse_result = yield parse_most_recent()
    yield Ribo.modify_comp(lambda a: a.set.parse_result(Just(parse_result)))
    display_result = yield Ribo.setting(display_parse_result)
    yield render_parse_result(parse_result) if display_result else NS.unit


__all__ = ('parse',)
