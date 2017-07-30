import abc
from collections import namedtuple
from types import FunctionType
from typing import Any, Tuple, Callable

from fn.recur import tco

from networkx import DiGraph

from amino import List, Maybe, Try, curried, Just, L, _, Right, Either, Lists
from amino.regex import Match
from amino.logging import Logger

from ribosome.record import re_field, field

from myo.logging import Logging
from myo.output.data import OutputEvent, OutputEntry
from myo.record import Record


class ParserBase(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def events(self, output: List[str]) -> List[OutputEvent]:
        ...


class EdgeData(Record):
    r = re_field()
    entry = field((type, FunctionType))

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.r, self.entry)

Step = namedtuple('Step', ['node', 'data', 'weight'])


# TODO log errors
@curried
def cons(logger: Logger, entry: type, match: Match) -> Maybe[OutputEntry]:
    return Try(entry, text=match.string, **match.group_map).leffect(logger.ddebug)


# memoize `edges()`
class SimpleParser(ParserBase, metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def graph(self) -> DiGraph:
        ...

    def event(self, entries: List[OutputEntry]) -> Maybe[OutputEvent]:
        return Just(OutputEvent(entries=entries))

    def edges(self, node: str) -> List[Step]:
        e = (Step(t, d['data'], d.get('weight', 0)) for f, t, d in self.graph.edges(node, data=True))
        return Lists.wrap(e)

    def match_edge(self, node: str, match: Callable[[Any], Either[str, OutputEntry]]) -> Either[str, OutputEntry]:
        return (
            self.edges(node)
            .sort_by(_.weight, reverse=True)
            .find_map(match)
        )

    @tco
    def _process(self, node: str, output: List[str], result: List[OutputEvent], current: List[OutputEntry]
                 ) -> List[OutputEvent]:
        '''
        Parse a list of output lines. Uses a trampoline for tail call
        elimination.
        The algorithm starts at the graph node 'start'
        1. detach the first output line into *line* and *rest* and call
           *parse_line*
        2. find an edge that matches to current line
        a) if a match was found
            3. construct an *OutputEntry*
            4. set the current node to the target node of the edge
            5. add the entry to the list *current*
            6. recurse with *rest* as new *output*
        b) if no match was found
            7. construct an *OutputEvent* from *current*
            8. if the current node is 'start', set *output* to *rest*
               else, keep *output* to try again with 'start'
            9. recurse with 'start'
        10. add the last event and exit the recursion
        '''
        def add_event() -> List[OutputEvent]:
            new = current.empty.no.flat_maybe_call(L(self.event)(current))
            return result + new.to_list
        def parse_line(line: str, rest: List[str]) -> Tuple[bool, tuple]:
            self.log.ddebug('parsing line: {}'.format(line))
            def match(step: Step) -> Either[str, Tuple[OutputEntry, str]]:
                def dbg(a: Any) -> None:
                    self.log.ddebug('matched edge to {}'.format, step.node)
                return (
                    step.data.r.match(line) %
                    dbg //
                    cons(self.log)(step.data.entry)
                ) & Right(step.node)
            def cont(entry: OutputEntry, next_node: str) -> Tuple[bool, tuple]:
                return True, (self, next_node, rest, result, current.cat(entry))
            def next_event() -> Tuple[bool, tuple]:
                new_output = rest if node == 'start' and current.empty else output
                return True, (self, 'start', new_output, add_event(), List())
            return self.match_edge(node, match).map2(cont) | next_event
        quit = lambda: (False, add_event())
        return output.detach_head.map2(parse_line) | quit

    def events(self, output: List[str]) -> List[OutputEvent]:
        return self._process(self, 'start', output, List(), List())

__all__ = ('ParserBase',)
