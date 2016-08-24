from collections import namedtuple

from networkx import DiGraph

from amino import List, Maybe, Just, curried, Try
from amino.lazy import lazy

from ribosome.record import field, re_field

from myo.output.parser.base import ParserBase
from myo.record import Record
from myo.output.data import PositionEntry, OutputEntry, ErrorEntry, OutputEvent


class FileEntry(PositionEntry):
    fun = field(str)


class EdgeData(Record):
    r = re_field()
    entry = field(type)

_file = EdgeData(
    r='  File "(?P<path>.+)", line (?P<line>\d+), in (?P<fun>\S+)',
    entry=FileEntry)
_expr = EdgeData(r='    (.+)', entry=OutputEntry)
_error = EdgeData(r='(?P<error>\S+): (?P<msg>\S+)', entry=ErrorEntry)

Step = namedtuple('Step', ['node', 'data'])


@curried
def cons(entry, match):
    return Try(entry, text=match.string, **match.groupdict()).to_maybe


class Parser(ParserBase):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'expr', data=_expr)
        g.add_edge('expr', 'file', data=_file)
        g.add_edge('expr', 'error', data=_error)
        return g

    def edges(self, node):
        e = (Step(t, d['data']) for f, t, d in self.graph.edges(node,
                                                                data=True))
        return List.wrap(e)

    def _process(self, node: str, output: List[str], result: List[OutputEvent],
                 current: List[OutputEntry]) -> List[OutputEvent]:
        def add_event():
            ev = OutputEvent(head='traceback', entries=current)
            new = current.empty.no.maybe(ev).to_list
            return result + new
        def parse_line(line: str, rest: List[str]):
            def match(step: Step):
                return (
                    Maybe(step.data.r.match(line)) //
                    cons(step.data.entry)
                ) & Just(step.node)
            def cont(entry: OutputEntry, next_node: str):
                return self._process(next_node, rest, result,
                                     current.cat(entry))
            def next_event():
                new_output = rest if node == 'start' else output
                return self._process('start', new_output, add_event(), List())
            return self.edges(node).find_map(match).map2(cont) | next_event
        return output.detach_head.map2(parse_line) | add_event()

    def events(self, output):
        return self._process('start', output, List(), List())

__all__ = ('Parser',)
