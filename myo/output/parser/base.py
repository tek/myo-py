from typing import Any, Tuple, Callable, Generic, TypeVar

from networkx import DiGraph

from amino import List, Maybe, curried, Just, _, Right, Either, Lists, Dat, Regex, Map, Nil, do, Do
from amino.regex import Match
from amino.func import tailrec
from amino.logging import module_log

from myo.output.data.output import OutputEvent, OutputLine

log = module_log()
A = TypeVar('A')
B = TypeVar('B')


class Parser(Generic[A, B], Dat['Parser[A, B]']):

    @staticmethod
    def cons(
            graph: DiGraph,
            cons_events: Callable[[List[OutputLine[A]]], List[OutputEvent[A, B]]],
    ) -> 'Parser':
        return Parser(
            graph,
            cons_events,
        )

    def __init__(self, graph: DiGraph, cons_events: Callable[[List[OutputLine[A]]], List[OutputEvent[A, B]]]) -> None:
        self.graph = graph
        self.cons_events = cons_events


class EdgeData(Generic[A], Dat['EdgeData[A]']):

    @staticmethod
    def strict(regex: Regex, cons_output_line: Callable[..., A]) -> 'EdgeData[A]':
        return EdgeData(regex, lambda *a, **kw: Right(cons_output_line(*a, **kw)))

    def __init__(self, regex: Regex, cons_output_line: Callable[..., Either[str, A]]) -> None:
        self.regex = regex
        self.cons_output_line = cons_output_line


class Step(Dat['Step']):

    def __init__(self, node: str, data: Map, weight: int) -> None:
        self.node = node
        self.data = data
        self.weight = weight


@curried
def cons_output_line(cons: Callable[..., Either[str, A]]) -> Callable[[Match], Either[str, OutputLine[A]]]:
    @do(Either[str, OutputLine[A]])
    def cons_output_line(match: Match) -> Do:
        data = yield cons(**match.group_map)
        return OutputLine(match.string, data)
    return cons_output_line


def simple_event(lines: List[OutputLine[A]]) -> Maybe[OutputEvent[A, B]]:
    return Just(OutputEvent(lines=lines))


def edges(graph: DiGraph, node: str) -> List[Step]:
    e = (Step(t, d['data'], d.get('weight', 0)) for f, t, d in graph.edges(node, data=True))
    return Lists.wrap(e)


def match_edge(
        graph: DiGraph,
        node: str,
        match: Callable[[Any], Either[str, OutputLine[A]]],
) -> Either[str, OutputLine[A]]:
    return (
        edges(graph, node)
        .sort_by(_.weight, reverse=True)
        .find_map_e(match)
    )


@tailrec
def simple_parse_process(
        parser: Parser[A, B],
        node: str,
        output: List[str],
        result: List[OutputEvent[A, B]],
        current: List[OutputLine[A]],
) -> List[OutputEvent[A, B]]:
    '''
    Parse a list of output lines.
    The algorithm starts at the graph node 'start'
    1. detach the first output line into *line* and *rest* and call
        *parse_line*
    2. find an edge that matches to current line
    a) if a match was found
        3. construct an *OutputLine*
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
    def add_event() -> List[OutputEvent[A, B]]:
        new = Nil if current.empty else parser.cons_events(current)
        return result + new
    def parse_line(line: str, rest: List[str]) -> Tuple[bool, tuple]:
        log.debug2(lambda: f'parsing line: {line}')
        @do(Either[str, Tuple[OutputLine[A], str]])
        def match(step: Step) -> Do:
            match = yield step.data.regex.match(line)
            log.debug2(lambda: f'matched edge to {step.node}')
            output_line = yield cons_output_line(step.data.cons_output_line)(match)
            return output_line, step.node
        def cont(entry: OutputLine[A], next_node: str) -> Tuple[bool, tuple]:
            return True, (parser, next_node, rest, result, current.cat(entry))
        def next_event() -> Tuple[bool, tuple]:
            new_output = rest if node == 'start' and current.empty else output
            return True, (parser, 'start', new_output, add_event(), List())
        return match_edge(parser.graph, node, match).map2(cont) | next_event
    quit = lambda: (False, add_event())
    return output.detach_head.map2(parse_line) | quit


def parse_events(parser: Parser[A, B], output: List[str]) -> Either[str, List[OutputEvent[A, B]]]:
    log.debug(f'parsing with {parser}')
    return Right(simple_parse_process(parser, 'start', output, Nil, Nil))


__all__ = ('parse_events', 'Parser', 'EdgeData', 'Step', 'cons_output_line',)
