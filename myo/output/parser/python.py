from typing import Tuple

from networkx import DiGraph

from amino.lazy import lazy
from amino import List, Empty, Just, Maybe, __, L, _

from ribosome.record import field, maybe_field

from myo.output.data import (PositionEntry, ErrorEntry, OutputEntry,
                             OutputEvent, OutputLine, MultiEvent)
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):
    fun = field(str)
    expr = maybe_field(str)

    def lines(self, event: OutputEvent):
        x = self.expr / L(OutputLine.create)(_, self)
        return super().lines(event) + x.to_list


class ExprEntry(OutputEntry):
    pass


class PyErrorEntry(ErrorEntry):
    exc = field(str)

_file = EdgeData(
    r='  File "(?P<path>.+)", line (?P<line>\d+), in (?P<fun>\S+)',
    entry=FileEntry
)
_expr = EdgeData(r='    (.+)', entry=ExprEntry)
_error = EdgeData(r='(?P<exc>\S+): (?P<error>.+)', entry=PyErrorEntry)


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'expr', data=_expr)
        g.add_edge('expr', 'file', data=_file)
        g.add_edge('expr', 'error', data=_error)
        return g

    def event(self, entries: List[OutputEntry]):
        def folder(z: Tuple[List[OutputEntry], Maybe[FileEntry]], a):
            res, cur = z
            add, new = (
                (cur, Just(a))
                if isinstance(a, FileEntry) else
                ((cur / __.set(expr=Just(a.text))).or_else(Just(a)), Empty())
                if isinstance(a, ExprEntry) else
                (Just(a), Empty())
            )
            return res + add.to_list, new
        grouped, rest = entries.fold_left((List(), Empty()))(folder)
        complete = grouped + rest.to_list
        return Just(MultiEvent(head=List('traceback'), entries=complete))

__all__ = ('Parser',)
