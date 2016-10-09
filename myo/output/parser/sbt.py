from networkx import DiGraph

from amino.lazy import lazy
from amino import List, _

from ribosome.record import field, maybe_field

from myo.output.data import (PositionEntry, OutputEntry, OutputEvent,
                             Location, CodeEntry as CodeEntryBase)
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):
    error = field(str)
    tag = field(str)

    @property
    def _str_extra(self):
        return super()._str_extra.cat(self.error)


class CodeEntry(CodeEntryBase):
    tag = field(str)


class ColEntry(OutputEntry):
    ws = field(str)
    tag = field(str)

    @property
    def _str_extra(self):
        return List(self.col)

    @property
    def col(self):
        return len(self.ws)


_msg_type = '\[(?P<tag>\w+)\] '
_file = EdgeData(
    r='^{}\s*(?P<path>[^:]+):(?P<line>\d+):\s*(?P<error>.*?);?$'
    .format(_msg_type),
    entry=FileEntry
)
_code = EdgeData(
    r='^{}(?P<code>\s*.+)'.format(_msg_type),
    entry=CodeEntry
)
_col = EdgeData(
    r='^{}(?P<ws>\s*)\^\s*'.format(_msg_type),
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
        return self.file.line, self.col / _.col | 1

    @property
    def code(self):
        return self.entries.filter_type(CodeEntry)


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'error', data=_code)
        g.add_edge('error', 'error', data=_code)
        g.add_edge('error', 'col', data=_col, weight=1)
        return g

    def event(self, entries: List[OutputEntry]):
        col = entries.find_type(ColEntry)
        return (
            entries.find_type(FileEntry) / (
                lambda a: SbtOutputEvent(head=List('error'), entries=entries,
                                         col=col, file=a)
            )
        )

__all__ = ('Parser',)
