from typing import Tuple

from networkx import DiGraph

from amino.lazy import lazy
from amino import List, Empty, Just, Maybe, __, L, _

from ribosome.record import field, maybe_field

from myo.output.data import (PositionEntry, ErrorEntry, OutputEntry,
                             OutputEvent, OutputLine, MultiEvent, CodeEntry)
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):
    fun = field(str)
    code = maybe_field(CodeEntry)

    def lines(self, event: OutputEvent):
        x = self.code / L(OutputLine.create)(_.text, self)
        return super().lines(event) + x.to_list


class PyErrorEntry(ErrorEntry):
    exc = field(str)

_file = EdgeData(
    r='  File "(?P<path>.+)", line (?P<line>\d+), in (?P<fun>\S+)',
    entry=FileEntry
)
_code = EdgeData(r='    (?P<code>.+)', entry=CodeEntry)
_error = EdgeData(r='(?P<exc>\S+): (?P<error>.+)', entry=PyErrorEntry)


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'code', data=_code)
        g.add_edge('code', 'file', data=_file)
        g.add_edge('code', 'error', data=_error)
        return g

    def event(self, entries: List[OutputEntry]):
        def folder(z: Tuple[List[OutputEntry], Maybe[FileEntry]], a):
            res, cur = z
            add, new = (
                (cur, Just(a))
                if isinstance(a, FileEntry) else
                ((cur / __.set(code=Just(a))).or_else(Just(a)), Empty())
                if isinstance(a, CodeEntry) else
                (Just(a), Empty())
            )
            return res + add.to_list, new
        grouped, rest = entries.fold_left((List(), Empty()))(folder)
        complete = grouped + rest.to_list
        return Just(MultiEvent(head=List('traceback'), entries=complete))

__all__ = ('Parser',)
