import abc
from typing import Callable

from amino import List, Path, Either, __, L, _, Just, Empty, Nil, do, Do
from amino.io import IO
from amino.lazy import lazy
from amino.logging import module_log
from amino.mod import instance_from_module

from ribosome import NvimApi
from ribosome.util.callback import VimCallback

from myo.logging import Logging
from myo.output.data.output import ParseResult, OutputEvent
from myo.output.parser.base import Parser, parse_events

log = module_log()
parsers_module = 'myo.output.parser'


def resolve_parsers(langs: List[str]) -> List[Parser]:
    modules = langs.flat_map(lambda a: Either.import_module(f'{parsers_module}.{a}').to_list)
    return modules.traverse(lambda a: instance_from_module(a, Parser), Either)


@do(Either[str, List[OutputEvent]])
def parsers_events(parsers: List[Parser], output: List[str]) -> Do:
    yield parsers.flat_traverse(lambda a: parse_events(a, output), Either)


@do(Either[str, List[OutputEvent]])
def parse_with_langs(output: List[str], langs: List[str]) -> Do:
    parsers = yield resolve_parsers(langs)
    yield parsers_events(parsers, output)


__all__ = ('parsers_events', 'parse_with_langs',)
