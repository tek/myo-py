import abc
from typing import Tuple, Callable, Union

from chiasma.util.id import Ident

from amino import _, Path, List, __, Empty, Just, L, Dat, Maybe, Nil
from amino.lazy import lazy

from myo.util import parse_int


class OutputEntry(Dat['OutputEntry']):

    def __init__(self, text: str) -> None:
        self.text = text

    @property
    def _str_name(self):
        return self._name.replace('Entry', '')

    def lines(self, event, group=Empty()):
        return self.format_lines(event, _.text, group)

    def format_lines(self, event, f: Callable, group=Empty()):
        return List(OutputLine.cons(f(self), event | self, self, group=group))


class OutputLine(Dat['OutputLine']):
    # target = any_field()
    # entry = optional_field(OutputEntry)
    # indent = dfield(0)
    # group = optional_field(str)

    @staticmethod
    def cons(
            text: str,
            target: Union[OutputEntry, 'OutputEvent'],
            entry: OutputEntry=None,
            indent: int=0,
            group: str=None,
    ):
        return OutputLine(text, target, Maybe.optional(entry), indent, Maybe.optional(group))

    def __init__(
            self,
            text: str,
            target: Union[OutputEntry, 'OutputEvent'],
            entry: Maybe[OutputEntry],
            indent: int,
            group: Maybe[str],
    ) -> None:
        self.text = text
        self.target = target
        self.entry = entry
        self.indent = indent
        self.group = group

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

    def __init__(self, text: str, error: str) -> None:
        self.text = text
        self.error = error


class CodeEntry(OutputEntry):

    def __init__(self, text: str, code: str) -> None:
        self.text = text
        self.code = code


def _parse_line(data):
    return data if isinstance(data, int) else parse_int(data) | 0


class Location:

    @abc.abstractproperty
    def file_path(self) -> Path:
        ...

    @abc.abstractproperty
    def coords(self) -> Tuple[int, int]:
        ...

    @property
    def nvim_coords(self) -> Tuple[int, int]:
        line, col = self.coords
        return line + 1, col

    @property
    def location(self) -> 'Location':
        return self

    def same_location(self, other):
        return isinstance(other, Location) and self.location == other.location


class PositionEntry(OutputEntry, Location):
    # line = field(int, factory=_parse_line)
    # col = dfield(0)

    def __init__(self, text: str, path: Path, line: int, col: int) -> None:
        self.text = text
        self.path = path
        self.line = line
        self.col = col

    @property
    def _str_extra(self):
        return List(self.path.name, self.coords)

    @property
    def file_path(self):
        return self.path

    @property
    def coords(self):
        return (self.line, self.col)


class OutputEvent(Dat['OutputEvent']):

    @staticmethod
    def cons(head: List[str]=Nil, entries: List[OutputEntry]=Nil) -> 'OutputEvent':
        return OutputEvent(head, entries)

    def __init__(self, head: List[str], entries: List[OutputEntry]) -> None:
        self.head = head
        self.entries = entries

    @property
    def _str_extra(self):
        return self.entries

    @property
    def _target(self):
        return Just(self)

    @property
    def lines(self):
        return (
            (self.head / L(OutputLine.cons)(_, self)) +
            (self.entries // __.lines(self._target))
        )

    @property
    def locations(self):
        return self.entries.filter_type(Location)


class MultiEvent(OutputEvent):

    @property
    def _target(self):
        return Empty()


class ParseResult(Dat['ParseResult']):

    def __init__(self, head: List[str], events: List[OutputEvent], langs: List[str]) -> None:
        self.head = head
        self.events = events
        self.langs = langs

    @lazy
    def lines(self):
        return (
            (self.head / L(OutputLine.cons)(_, self)) +
            (self.events // _.lines)
        )

    @property
    def display_lines(self):
        return self.lines / _.formatted

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

    @property
    def locations(self):
        return self.events // _.locations


__all__ = ('OutputEntry', 'OutputEvent', 'ParseResult')
