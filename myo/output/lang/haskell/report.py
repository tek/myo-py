from typing import Any

from lark import Lark, Tree
from lark.lexer import Token

from amino import List, do, Do, Nil, Try, Either, Lists, Right, Left, Maybe
from amino.logging import module_log

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.data.output import OutputEvent, Location
from myo.components.command.compute.parse_handlers import PathFormatter
from myo.output.data.report import DisplayLine, PlainDisplayLine
from myo.output.parser.haskell import HaskellEvent, HaskellLine
from myo.output.lang.haskell.grammar import grammar

from ribosome.nvim.io.state import NS

log = module_log()
parser = Lark(grammar)  # type: ignore


@do(NS[CommandRibosome, List[DisplayLine]])
def format_location(location: Location, path_formatter: PathFormatter) -> Do:
    path = yield path_formatter(location.path)
    return List(PlainDisplayLine(f'{path}  {location.line + 1}'))


def tfilt(tree: Tree, key: str) -> List[Tree]:
    return Lists.wrap(tree.children).filter(lambda c: isinstance(c, Tree) and c.data == key)


def first(trees: List[Tree]) -> List[Tree]:
    return trees.flat_map(lambda a: Lists.wrap(a.children).head)


def token_values(trees: List[Any]) -> List[str]:
    return trees.filter_type(Token).map(lambda a: a.value)


def tnames(tree: Tree) -> List[str]:
    return token_values(first(tfilt(tree, 'name')))


def qnamedata(tree: Tree) -> Maybe[str]:
    return token_values(first(tfilt(tree, 'qnamedata'))).head


def qnames(tree: Tree) -> List[str]:
    return tfilt(tree, 'qname').flat_map(qnamedata)


def tlift(tree: Tree, key: str) -> Either[str, Tree]:
    return tfilt(tree, key).head.to_either(f'no child `key`')


@do(Either[str, List[Tree]])
def foundreq(tree: Tree) -> Do:
    req, found = yield qnames(tree).lift_all(0, 1).to_either('invalid name count')
    return List(
        'type mismatch',
        found.replace("\n", ' '),
        req.replace("\n", ' '),
    )


@do(Either[str, List[Tree]])
def notypeclass(tree: Tree) -> Do:
    pt = yield tlift(tree, 'parenstype')
    names = tnames(pt)
    tc, tpe = yield names.lift_all(0, 1).to_either('too few names')
    trigger = yield qnames(tree).head.to_either('no trigger')
    return List(
        f'!instance: {trigger}',
        f'{tc} {tpe}'
    )


@do(Either[str, List[str]])
def from_grammar(lines: List[str]) -> Do:
    tree = yield Try(parser.parse, lines.join_lines)
    spec = yield tlift(tree, 'specific')
    candidate = yield Lists.wrap(spec.children).head.to_either('empty specific')
    dotted = yield (
        Lists.wrap(candidate.children).lift(1).to_either('empty dotted')
        if candidate.data == 'dotted' else
        Left('candidate is not dotted')
    )
    tpe = dotted.data
    yield (
        foundreq(dotted)
        if tpe == 'foundreq' else
        notypeclass(dotted)
        if tpe == 'notypeclass' else
        Right(Nil)
    )


def format_info(lines: List[str]) -> List[str]:
    return from_grammar(lines).get_or_strict(lines)


@do(NS[CommandRibosome, List[DisplayLine]])
def haskell_report(path_formatter: PathFormatter, output: OutputEvent[HaskellLine, HaskellEvent]) -> Do:
    info = format_info(output.meta.info.map(lambda a: a.meta.message)).indent(2).map(PlainDisplayLine)
    location = yield output.location.map(lambda a: format_location(a, path_formatter)).get_or(NS.pure, Nil)
    return location + info


__all__ = ('haskell_report',)
