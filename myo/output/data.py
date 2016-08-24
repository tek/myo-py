from amino import _, Path

from ribosome.record import field, list_field, dfield

from myo.record import Record
from myo.util import parse_int


class OutputEntry(Record):
    text = field(str)

    @property
    def formatted(self):
        return self.text


class ErrorEntry(OutputEntry):
    error = field(str)
    msg = field(str)


def _parse_line(data):
    if isinstance(data, int):
        return data
    else:
        return parse_int(data) | 0


class PositionEntry(OutputEntry):
    path = field(Path, factory=Path)
    line = field(int, factory=_parse_line)
    col = dfield(0)


class OutputEvent(Record):
    head = field(str)
    entries = list_field(OutputEntry)

    @property
    def display_lines(self):
        return (self.entries / _.formatted).cons(self.head)


class ParseResult(Record):
    head = field(str)
    events = list_field(OutputEvent)

    @property
    def display_lines(self):
        return (self.events // _.display_lines).cons(self.head)

__all__ = ('OutputEntry', 'OutputEvent', 'ParseResult')
