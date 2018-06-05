from types import ModuleType

from amino import List, Either, do, Do
from amino.logging import module_log
from amino.mod import instance_from_module

from myo.output.data.output import OutputEvent
from myo.output.parser.base import Parser, parse_events

log = module_log()
parsers_module = 'myo.output.parser'


def resolve_parsers(langs: List[str]) -> List[Parser]:
    def imp(mod: str) -> List[ModuleType]:
        return Either.import_module(f'{parsers_module}.{mod}').or_else_call(Either.import_module, mod).to_list
    modules = langs.flat_map(imp)
    return modules.traverse(lambda a: instance_from_module(a, Parser), Either)


@do(Either[str, List[OutputEvent]])
def parsers_events(parsers: List[Parser], output: List[str]) -> Do:
    yield parsers.flat_traverse(lambda a: parse_events(a, output), Either)


@do(Either[str, List[OutputEvent]])
def parse_with_langs(output: List[str], langs: List[str]) -> Do:
    parsers = yield resolve_parsers(langs)
    yield parsers_events(parsers, output)


__all__ = ('parsers_events', 'parse_with_langs',)
