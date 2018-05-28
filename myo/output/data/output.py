from typing import Union, Generic, TypeVar, Tuple

from amino import Path, List, Dat, Maybe, Nil, Nothing

A = TypeVar('A')


class OutputLine(Generic[A], Dat['OutputLine']):

    def __init__(self, text: str, meta: A, indent: int=0) -> None:
        self.text = text
        self.meta = meta
        self.indent = indent


class OutputLineOld(Dat['OutputLineOld']):

    def __init__(
            self,
            text: str,
            target: Union[OutputLine, 'OutputEvent'],
            entry: Maybe[OutputLine],
            indent: int,
            group: Maybe[str],
    ) -> None:
        self.text = text
        self.target = target
        self.entry = entry
        self.indent = indent
        self.group = group


class Location(Dat['Location']):

    @staticmethod
    def cons(
            path: Path,
            line: int,
            col: int,
    ) -> 'Location':
        return Location(
            path,
            line,
            col,
        )

    def __init__(self, path: Path, line: int, col: int) -> None:
        self.path = path
        self.line = line
        self.col = col

    @property
    def coords(self) -> Tuple[int, int]:
        return self.line, self.col


class OutputEvent(Generic[A], Dat['OutputEvent[A]']):

    @staticmethod
    def cons(
            lines: List[OutputLine[A]]=Nil,
            location: Maybe[Location]=Nothing,
            head: List[str]=Nil,
    ) -> 'OutputEvent[A]':
        return OutputEvent(lines, location, head)

    def __init__(self, lines: List[OutputLine[A]], location: Maybe[Location], head: List[str]) -> None:
        self.lines = lines
        self.location = location
        self.head = head


class ParseResult(Generic[A], Dat['ParseResult']):

    def __init__(self, head: List[str], events: List[OutputEvent[A]]) -> None:
        self.head = head
        self.events = events


__all__ = ('OutputLine', 'OutputEvent', 'ParseResult')
