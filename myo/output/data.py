from amino import _, Path, List
from amino.lazy import lazy

from ribosome.record import field, list_field, dfield, any_field

from myo.record import Record
from myo.util import parse_int


class OutputEntry(Record):
    text = field(str)

    @property
    def output_lines(self):
        return List(OutputLine.create(self.text, self))


class OutputLine(Record):
    text = field(str)
    target = any_field()

    @staticmethod
    def create(text, target):
        return OutputLine(text=text, target=target)


class ErrorEntry(OutputEntry):
    error = field(str)
    msg = field(str)


def _parse_line(data):
    return data if isinstance(data, int) else parse_int(data) | 0


class PositionEntry(OutputEntry):
    path = field(Path, factory=Path)
    line = field(int, factory=_parse_line)
    col = dfield(0)


class OutputEvent(Record):
    head = field(str)
    entries = list_field(OutputEntry)

    @property
    def lines(self):
        return (
            (self.entries // _.output_lines)
            .cons(OutputLine.create(self.head, self))
        )


class ParseResult(Record):
    head = field(str)
    events = list_field(OutputEvent)

    @lazy
    def lines(self):
        return (
            (self.events // _.lines)
            .cons(OutputLine.create(self.head, self))
        )

    @property
    def display_lines(self):
        return self.lines / _.text

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

__all__ = ('OutputEntry', 'OutputEvent', 'ParseResult')
