import abc
from typing import Any, Tuple, Callable

from networkx import DiGraph

from amino import List, Maybe, curried, Just, _, Right, Either, Lists, Dat, Regex, Nothing, Map
from amino.regex import Match
from amino.func import tailrec

from myo.logging import Logging
from myo.output.data import OutputEvent, OutputEntry


class ParserBase(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def events(self, output: List[str]) -> List[OutputEvent]:
        ...


class EdgeData(Dat['EdgeData']):

    @staticmethod
    def strict(r: Regex, cons_entry: Callable[..., Either[str, OutputEntry]]) -> 'EdgeData':
        return EdgeData(r, lambda *a, **kw: Right(cons_entry(*a, **kw)))

    def __init__(self, r: Regex, cons_entry: Callable[..., Either[str, OutputEntry]]) -> None:
        self.r = r
        self.cons_entry = cons_entry


class Step(Dat['Step']):

    def __init__(self, node: str, data: Map, weight: int) -> None:
        self.node = node
        self.data = data
        self.weight = weight


@curried
def cons_entry(
        cons_entry: Callable[..., Either[str, OutputEntry]],
        match: Match,
) -> Either[str, OutputEntry]:
    return cons_entry(text=match.string, **match.group_map)


class SimpleParser(ParserBase, abc.ABC):

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
            .find_map_e(match)
        )

    @tailrec
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
            new = Nothing if current.empty else self.event(current)
            return result + new.to_list
        def parse_line(line: str, rest: List[str]) -> Tuple[bool, tuple]:
            self.log.debug2(lambda: f'parsing line: {line}')
            def match(step: Step) -> Either[str, Tuple[OutputEntry, str]]:
                def dbg(a: Any) -> None:
                    self.log.debug2(lambda: f'matched edge to {step.node}')
                return (
                    step.data.r.match(line) %
                    dbg //
                    cons_entry(step.data.cons_entry)
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
