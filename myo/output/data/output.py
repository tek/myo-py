from typing import Union, Generic, TypeVar, Tuple

from amino import Path, List, Dat, Maybe, Nil, Nothing

A = TypeVar('A')
B = TypeVar('B')


class OutputLine(Generic[A], Dat['OutputLine']):

    def __init__(self, text: str, meta: A, indent: int=0) -> None:
        self.text = text
        self.meta = meta
        self.indent = indent


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


class OutputEvent(Generic[A, B], Dat['OutputEvent[A, B]']):

    @staticmethod
    def cons(
            meta: B,
            lines: List[OutputLine[A]]=Nil,
            location: Maybe[Location]=Nothing,
            head: List[str]=Nil,
    ) -> 'OutputEvent[A]':
        return OutputEvent(meta, lines, location, head)

    def __init__(self, meta: B, lines: List[OutputLine[A]], location: Maybe[Location], head: List[str]) -> None:
        self.meta = meta
        self.lines = lines
        self.location = location
        self.head = head


__all__ = ('OutputLine', 'OutputEvent')
