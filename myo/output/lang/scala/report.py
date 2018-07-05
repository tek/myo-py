from typing import Tuple

from amino import List, do, Do, Nil, Maybe, Lists, Dat, Eval, Just
from amino.util.string import indent
from amino.logging import module_log
from amino.util.numeric import add, sub

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.data.output import OutputEvent, Location, OutputLine
from myo.components.command.compute.parse_handlers import PathFormatter
from myo.output.data.report import DisplayLine, PlainDisplayLine
from myo.output.parser.scala import ScalaEvent, ScalaLine, ColLine, CodeLine

from ribosome.nvim.io.state import NS

log = module_log()
col_marker = '†'
foundreq_separator = ' | '
found_marker = '+'
separator_marker = '<'
req_marker = '-'


@do(NS[CommandRibosome, List[DisplayLine]])
def format_location(location: Location, path_formatter: PathFormatter) -> Do:
    path = yield path_formatter(location.path)
    return List(PlainDisplayLine(f'{path}  {location.line}'))


def inject_col_marker(code_line: CodeLine, col_line: Maybe[OutputLine[ColLine]]) -> str:
    col = col_line.map(lambda a: a.meta.col).get_or_strict(0) - code_line.indent
    return f'{code_line.code[:col]}{col_marker}{code_line.code[col:]}'


class BracketState(Dat['BracketState']):

    @staticmethod
    def cons(
            match: int=None,
            index: int=0,
            parens: int=0,
            square: int=0,
    ) -> 'BracketState':
        return BracketState(
            Maybe.optional(match),
            index,
            parens,
            square,
        )

    def __init__(self, match: Maybe[int], index: int, parens: int, square: int) -> None:
        self.match = match
        self.index = index
        self.parens = parens
        self.square = square

    def push_square(self) -> 'BracketState':
        return self.mod.square(add(1))

    def push_parens(self) -> 'BracketState':
        return self.mod.parens(add(1))

    def pop_square(self) -> 'BracketState':
        return self.set.match(Just(self.index)) if self.square == 0 else self.mod.square(sub(1))

    def pop_parens(self) -> 'BracketState':
        return self.set.match(Just(self.index)) if self.parens == 0 else self.mod.parens(sub(1))


def limiting_bracket(chars: List[str], brackets: Tuple[str, str, str, str]) -> Maybe[int]:
    o_square, c_square, o_parens, c_parens = brackets
    def folder(z: BracketState, a: str) -> Eval[BracketState]:
        def step() -> BracketState:
            next = (
                z.push_square()
                if a == c_square else
                z.push_parens()
                if a == c_parens else
                z.pop_square()
                if a == o_square else
                z.pop_parens()
                if a == c_parens else
                z
            )
            return next.mod.index(add(1))
        return Eval.now(z.match.replace(z).get_or(step))
    result = chars.fold_m(Eval.now(BracketState.cons()))(folder)
    return result.evaluate().match


def opening_bracket(line: str, index: int) -> int:
    chars = Lists.wrap(line[:index]).reversed
    result = limiting_bracket(chars, ('[', ']', '(', ')'))
    return result.map(lambda a: index - a).get_or_strict(0)


def closing_bracket(line: str, index: int) -> int:
    chars = Lists.wrap(line[index:])
    result = limiting_bracket(chars, (']', '[', ')', '('))
    return result.map(lambda a: index + a).get_or_strict(0)


def foundreq_boundaries(line: str, index: int) -> Tuple[int, int, int]:
    opening = opening_bracket(line, index)
    closing = closing_bracket(line, index)
    return opening, index, closing


def insert_bound_markers(line: str, bounds: Tuple[int, int, int]) -> str:
    start, separator, end = bounds
    left = f'{line[:start]}{found_marker}{line[start:separator]}{separator_marker}'
    right = f'{line[separator:end]}{req_marker}{line[end:]}'
    return left + right


def handle_foundreq(line: str) -> str:
    indexes = Lists.find_str_matches(line, foundreq_separator).reversed
    bounds = indexes.map(lambda a: foundreq_boundaries(line, a))
    return bounds.fold_left(line)(insert_bound_markers)


@do(NS[CommandRibosome, List[DisplayLine]])
def scala_report(path_formatter: PathFormatter, output: OutputEvent[ScalaLine, ScalaEvent]) -> Do:
    code = (
        output.meta.code
        .map(lambda a: indent(inject_col_marker(a.meta, output.meta.col)))
        .map(PlainDisplayLine)
    )
    info = output.meta.info.map(lambda a: handle_foundreq(a.meta.message)).indent(2).map(PlainDisplayLine)
    location = yield output.location.map(lambda a: format_location(a, path_formatter)).get_or(NS.pure, Nil)
    error = PlainDisplayLine(output.meta.file.meta.error)
    return location.cat(error) + info + code.to_list


__all__ = ('scala_report',)
