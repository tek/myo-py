import abc
from typing import Tuple, Callable

from amino import _, Path, List, __, Empty, Just, L
from amino.lazy import lazy

from ribosome.record import (field, list_field, dfield, any_field, RecordMeta,
                             maybe_field)

from myo.record import Record
from myo.util import parse_int


class OutputEntry(Record):
    text = field(str)

    @property
    def _str_name(self):
        return self._name.replace('Entry', '')

    def lines(self, event, group=Empty()):
        return self.format_lines(event, _.text, group)

    def format_lines(self, event, f: Callable, group=Empty()):
        return List(OutputLine.create(f(self), event | self, Just(self),
                                      group=group))


class OutputLine(Record):
    text = field(str)
    target = any_field()
    entry = maybe_field(OutputEntry)
    indent = dfield(0)
    group = maybe_field(str)

    def __str__(self):
        return '{}({})'.format(self._name, self.text)

    @staticmethod
    def create(text, target, entry=Empty(), group=Empty()):
        return OutputLine(text=text, target=target, entry=entry, group=group)

    @property
    def formatted(self):
        return '{}{}'.format(' ' * self.indent, self.text)

    @property
    def syntax_group(self):
        return self.group.o(self.entry / __._name.replace('Entry', ''))


class EmptyLine(OutputLine):

    @staticmethod
    def create(target):
        return EmptyLine(text='', target=target)


class ErrorEntry(OutputEntry):
    error = field(str)


class CodeEntry(OutputEntry):
    code = field(str)


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
    def _str_extra(self):
        return List(self.path.name, self.coords)

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
    def _str_extra(self):
        return self.entries

    @property
    def _target(self):
        return Just(self)

    @property
    def lines(self):
        return (
            (self.head / L(OutputLine.create)(_, self)) +
            (self.entries // __.lines(self._target))
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
        return self.lines / _.formatted

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

__all__ = ('OutputEntry', 'OutputEvent', 'ParseResult')
