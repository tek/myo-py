from networkx import DiGraph

from amino.lazy import lazy

from ribosome.record import field

from myo.output.data import PositionEntry, ErrorEntry, OutputEntry
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):
    fun = field(str)

_file = EdgeData(
    r='  File "(?P<path>.+)", line (?P<line>\d+), in (?P<fun>\S+)',
    entry=FileEntry
)
_expr = EdgeData(r='    (.+)', entry=OutputEntry)
_error = EdgeData(r='(?P<error>\S+): (?P<msg>\S+)', entry=ErrorEntry)


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'expr', data=_expr)
        g.add_edge('expr', 'file', data=_file)
        g.add_edge('expr', 'error', data=_error)
        return g

__all__ = ('Parser',)
