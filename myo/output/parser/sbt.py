import operator

from networkx import DiGraph

from amino.lazy import lazy
from amino import List

from ribosome.record import field, maybe_field

from myo.output.data import (PositionEntry, OutputEntry, OutputEvent,
                             ErrorEntry, Location)
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):
    error = field(str)


class ColEntry(OutputEntry):

    @property
    def col(self):
        return (
            (self.msg.index_of('^') & self.msg.index_of(']')) /
            operator.sub |
            1
        )


_msg_type = '\[\w+\]\s*'
_file = EdgeData(
    r='^{}(?P<path>[^:]+):(?P<line>\d+):\s*(?P<error>.*?);?$'
    .format(_msg_type),
    entry=FileEntry
)
_error = EdgeData(
    r='^{}\s*(?P<error>.+)'.format(_msg_type),
    entry=ErrorEntry
)
_col = EdgeData(
    r='^{}\s*\^\s*'.format(_msg_type),
    entry=ColEntry
)


class SbtOutputEvent(OutputEvent, Location):
    col = maybe_field(ColEntry)
    file = field(FileEntry)

    @property
    def file_path(self):
        return self.file.file_path

    @property
    def coords(self):
        return self.file.line, self.col | 1


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'error', data=_error)
        g.add_edge('error', 'error', data=_error)
        g.add_edge('error', 'col', data=_col, weight=1)
        return g

    def event(self, entries: List[OutputEntry]):
        col = entries.find_type(ColEntry)
        return (
            entries.find_type(FileEntry) / (
                lambda a: SbtOutputEvent(head='error', entries=entries,
                                         col=col, file=a)
            )
        )

__all__ = ('Parser',)
