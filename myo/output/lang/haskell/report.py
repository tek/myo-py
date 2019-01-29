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


def first(tree: Tree) -> Maybe[Tree]:
    return Lists.wrap(tree.children).head


def firsts(trees: List[Tree]) -> List[Tree]:
    return trees.flat_map(first)


def token_values(trees: List[Any]) -> List[str]:
    return trees.filter_type(Token).map(lambda a: a.value)


def tree_tokens(tree: Tree, key: str) -> List[str]:
    return token_values(tfilt(tree, key).flat_map(lambda a: Lists.wrap(a.children)))


def tnames(tree: Tree) -> List[str]:
    return token_values(firsts(tfilt(tree, 'name')))


def first_token(tree: Tree, key: str) -> Maybe[str]:
    return token_values(firsts(tfilt(tree, key))).head


def qnamedata(tree: Tree) -> Maybe[str]:
    return token_values(firsts(tfilt(tree, 'qnamedata'))).head


def qnames(tree: Tree) -> List[str]:
    return tfilt(tree, 'qname').flat_map(qnamedata)


def tlift(tree: Tree, key: str) -> Either[str, Tree]:
    return tfilt(tree, key).head.to_either(f'no child `{key}`')


@do(Either[str, List[str]])
def foundreq(tree: Tree) -> Do:
    req, found = yield qnames(tree).lift_all(0, 1).to_either('invalid name count')
    return List(
        'type mismatch',
        found.replace("\n", ' '),
        req.replace("\n", ' '),
    )


@do(Either[str, List[str]])
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
def notinscope(tree: Tree) -> Do:
    name = yield first_token(tree, 'name').to_either('no name for notinscope')
    types = tree_tokens(tree, 'type').map(lambda a: a.strip())
    return List(f'Variable not in scope: {name} :: {types.join_tokens}')


def generic(tree: Tree) -> Either[str, List[str]]:
    return Right(firsts(tfilt(tree, 'any')).flat_map(Lists.lines).map(lambda a: a.strip()))


def dotted(tree: Tree) -> Either[str, List[str]]:
    tpe = tree.data
    return (
        foundreq(tree)
        if tpe == 'foundreq' else
        notypeclass(tree)
        if tpe == 'notypeclass' else
        notinscope(tree)
        if tpe == 'notinscope' else
        generic(tree)
        if tpe == 'genericdot' else
        Left('invalid dotted')
    )


def undotted(tree: Tree) -> Either[str, List[str]]:
    tpe = tree.data
    return (
        notinscope(tree)
        if tpe == 'notinscope' else
        Left('invalid undotted')
    )


@do(Either[str, List[str]])
def specific(tree: Tree) -> Do:
    candidate = yield first(tree).to_either('empty specific')
    yield (
        Lists.wrap(candidate.children).lift(1).to_either('empty dotted').flat_map(dotted)
        if candidate.data == 'dotted' else
        first(candidate).to_either('empty undotted').flat_map(undotted)
        if candidate.data == 'undotted' else
        Left('invalid specific')
    )


@do(Either[str, List[str]])
def from_grammar(lines: List[str]) -> Do:
    tree = yield Try(parser.parse, lines.join_lines)
    spec = yield tlift(tree, 'specific')
    yield specific(spec)


def log_error(error: str) -> None:
    log.debug(f'haskell report failed: {error}')


def format_info(lines: List[str]) -> List[str]:
    return from_grammar(lines).lmap(log_error).get_or_strict(lines)


@do(NS[CommandRibosome, List[DisplayLine]])
def haskell_report(path_formatter: PathFormatter, output: OutputEvent[HaskellLine, HaskellEvent]) -> Do:
    info = format_info(output.meta.info.map(lambda a: a.meta.message)).indent(2).map(PlainDisplayLine)
    location = yield output.location.map(lambda a: format_location(a, path_formatter)).get_or(NS.pure, Nil)
    return location + info


__all__ = ('haskell_report',)
