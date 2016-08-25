from collections import namedtuple
import abc

from myo.logging import Logging
from myo.output.data import OutputEvent, OutputEntry
from myo.record import Record

from amino import List, Maybe, Try, curried, Just, L

from ribosome import NvimFacade
from ribosome.record import re_field, field


class ParserBase(Logging, metaclass=abc.ABCMeta):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    @abc.abstractmethod
    def events(self, output: List[str]) -> List[OutputEvent]:
        ...


class EdgeData(Record):
    r = re_field()
    entry = field(type)

Step = namedtuple('Step', ['node', 'data'])


@curried
def cons(entry, match):
    return Try(entry, text=match.string, **match.groupdict()).to_maybe


class SimpleParser(ParserBase, metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def graph(self):
        ...

    def event(self, entries: List[OutputEntry]):
        return Just(OutputEvent(head='traceback', entries=entries))

    def edges(self, node):
        e = (Step(t, d['data']) for f, t, d in self.graph.edges(node,
                                                                data=True))
        return List.wrap(e)

    def _process(self, node: str, output: List[str], result: List[OutputEvent],
                 current: List[OutputEntry]) -> List[OutputEvent]:
        def add_event():
            new = current.empty.no.flat_maybe_call(L(self.event)(current))
            return result + new.to_list
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

__all__ = ('ParserBase',)
