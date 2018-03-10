from typing import Tuple, Union

from networkx import DiGraph

from amino.lazy import lazy
from amino import List, Empty, Just, Maybe, __, L, _, Path, Regex, Nothing, do, Either, Do, Try
from amino.util.numeric import parse_int

from myo.output.data import PositionEntry, ErrorEntry, OutputEntry, OutputEvent, OutputLine, MultiEvent, CodeEntry
from myo.output.parser.base import EdgeData, SimpleParser


class FileEntry(PositionEntry):

    @staticmethod
    @do(Either[str, 'FileEntry'])
    def cons(
            text: str,
            path: Union[str, Path],
            line: Union[str, int],
            col: Union[str, int]=0,
            fun: str=None,
    ) -> Do:
        path_p = yield Try(Path, path)
        line_i = yield parse_int(line)
        col_i = yield parse_int(col)
        return FileEntry(text=text, path=path_p, line=line_i, col=col_i, fun=Maybe.optional(fun), code=Nothing)

    def __init__(self, text: str, path: Path, line: int, col: int, fun: Maybe[str], code: Maybe[CodeEntry]) -> None:
        super().__init__(text, path, line, col)
        self.fun = fun
        self.code = code

    def lines(self, event: OutputEvent, group=Empty()):
        x = self.code / L(OutputLine.cons)(_.text, self)
        return super().lines(event) + x.to_list


class PyErrorEntry(ErrorEntry):

    def __init__(self, text: str, error: str, exc: str) -> None:
        super().__init__(text, error)
        self.exc = exc


class ColEntry(OutputEntry):

    def __init__(self, text: str, ws: str) -> None:
        super().__init__(text)
        self.ws = ws

    def lines(self, event: OutputEvent, group=Empty()):
        return List()


_file = EdgeData(
    r=Regex('\s*File "(?P<path>.+)", line (?P<line>\d+)(?:, in (?P<fun>\S+))?'),
    cons_entry=FileEntry.cons
)
_code = EdgeData.strict(r=Regex('^\s*(?P<code>.+)'), cons_entry=CodeEntry)
_error = EdgeData.strict(r=Regex('^\s*(?P<exc>\S+): (?P<error>.+)'), cons_entry=PyErrorEntry)
_col = EdgeData.strict(r=Regex('^\s*(?P<ws>\s+)\^'), cons_entry=ColEntry)


class Parser(SimpleParser):

    @lazy
    def graph(self):
        g = DiGraph()
        g.add_edge('start', 'file', data=_file)
        g.add_edge('file', 'code', data=_code)
        g.add_edge('code', 'file', data=_file)
        g.add_edge('code', 'error', data=_error)
        g.add_edge('code', 'col', data=_col)
        g.add_edge('col', 'error', data=_error)
        return g

    def event(self, entries: List[OutputEntry]):
        def folder(z: Tuple[List[OutputEntry], Maybe[FileEntry]], a):
            res, cur = z
            add, new = (
                (cur, Just(a))
                if isinstance(a, FileEntry) else
                ((cur / __.set.code(Just(a))).or_else(Just(a)), Empty())
                if isinstance(a, CodeEntry) else
                (Just(a), Empty())
            )
            return res + add.to_list, new
        grouped, rest = entries.fold_left((List(), Empty()))(folder)
        complete = grouped + rest.to_list
        return Just(MultiEvent.cons(entries=complete))

__all__ = ('Parser',)
