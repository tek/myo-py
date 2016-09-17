import abc
from typing import Tuple

from amino import _, Path, List, __, Empty, Just, L
from amino.lazy import lazy

from ribosome.record import field, list_field, dfield, any_field, RecordMeta

from myo.record import Record
from myo.util import parse_int


class OutputEntry(Record):
    text = field(str)

    def output_lines(self, event):
        return List(OutputLine.create(self.text, event | self))


class OutputLine(Record):
    text = field(str)
    target = any_field()

    @staticmethod
    def create(text, target):
        return OutputLine(text=text, target=target)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.text)


class ErrorEntry(OutputEntry):
    error = field(str)


def _parse_line(data):
    return data if isinstance(data, int) else parse_int(data) | 0


class LocationMeta(abc.ABCMeta, RecordMeta):
    pass


class Location:

    def file_path(self) -> Path:
        ...

    def coords(self) -> Tuple[int, int]:
        ...


class PositionEntry(OutputEntry, Location):
    path = field(Path, factory=Path)
    line = field(int, factory=_parse_line)
    col = dfield(0)

    @property
    def file_path(self):
        return self.path

    @property
    def coords(self):
        return (self.line, self.col)


class OutputEvent(Record):
    head = list_field(str)
    entries = list_field(OutputEntry)

    @property
    def _target(self):
        return Just(self)

    @property
    def lines(self):
        return (
            (self.head / L(OutputLine.create)(_, self)) +
            (self.entries // __.output_lines(self._target))
        )


class MultiEvent(OutputEvent):

    @property
    def _target(self):
        return Empty()


class ParseResult(Record):
    head = list_field(str)
    events = list_field(OutputEvent)
    langs = list_field(str)

    @lazy
    def lines(self):
        return (
            (self.head / L(OutputLine.create)(_, self)) +
            (self.events // _.lines)
        )

    @property
    def display_lines(self):
        return self.lines / _.text

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

__all__ = ('OutputEntry', 'OutputEvent', 'ParseResult')
