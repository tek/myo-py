from typing import Union

from networkx import DiGraph

from amino import List, Path, do, Either, Try, Do, Maybe, Regex, Nil, ADT, Just, Dat
from amino.util.numeric import parse_int
from amino.logging import module_log

from myo.output.data.output import OutputLine, OutputEvent, Location
from myo.output.parser.base import EdgeData, Parser

log = module_log()


class HaskellLine(ADT['HaskellLine']):
    pass


class FileLine(HaskellLine):

    @staticmethod
    @do(Either[str, 'FileLine'])
    def cons(
            path: Union[str, Path],
            line: Union[str, int],
            col: Union[str, int]=None,
    ) -> Do:
        path_p = yield Try(Path, path)
        line_i = yield parse_int(line)
        col_i = yield parse_int(1 if col is None else col)
        return FileLine(path_p, line_i - 1, col_i - 1)

    def __init__(self, path: Path, line: int, col: int) -> None:
        self.path = path
        self.line = line
        self.col = col


class InfoLine(HaskellLine):

    @staticmethod
    def cons(message: str, ws: str='', tag: str='') -> 'InfoLine':
        return InfoLine(message, len(ws), tag)

    def __init__(self, message: str, indent: int, tag: str) -> None:
        self.message = message
        self.indent = indent
        self.tag = tag


class CodeLine(HaskellLine):

    def __init__(self, code: str, indent: int, tag: str) -> None:
        self.code = code
        self.indent = indent
        self.tag = tag


_msg_type = '\[(?P<tag>\w+)\] '
file_edge: EdgeData[FileLine] = EdgeData(
    regex=Regex(f'^(?P<path>/[^:]+):(?P<line>\d+):((?P<col>\d+):)?'),
    cons_output_line=FileLine.cons,
)
info_edge = EdgeData.strict(
    regex=Regex(f'^(?P<ws>\s*)(?P<message>\s*.+)'),
    cons_output_line=InfoLine.cons,
)


class HaskellEvent(Dat['HaskellEvent']):

    @staticmethod
    def cons(
            file: OutputLine[FileLine],
            info: List[OutputLine[InfoLine]]=Nil,
    ) -> 'HaskellEvent':
        return HaskellEvent(file, info)

    def __init__(
            self,
            file: OutputLine[FileLine],
            info: List[OutputLine[InfoLine]],
    ) -> None:
        self.file = file
        self.info = info


def haskell_graph() -> DiGraph:
    g = DiGraph()  # type: ignore
    g.add_edge('start', 'file', data=file_edge)
    g.add_edge('file', 'info', data=info_edge)
    g.add_edge('info', 'info', data=info_edge)
    return g


@do(Maybe[OutputEvent[HaskellLine, HaskellEvent]])
def haskell_event(lines: List[OutputLine[HaskellLine]]) -> Do:
    file = yield lines.find(lambda a: isinstance(a.meta, FileLine))
    info = lines.filter(lambda a: isinstance(a.meta, InfoLine))
    location = Location(file.meta.path, file.meta.line, file.meta.col)
    return OutputEvent.cons(HaskellEvent(file, info), lines, Just(location))


def haskell_events(lines: List[OutputLine[HaskellLine]]) -> List[OutputEvent[HaskellLine, HaskellEvent]]:
    return haskell_event(lines).cata_strict(List, Nil)


haskell_parser = Parser(haskell_graph(), haskell_events)

__all__ = ('haskell_parser',)
