from typing import Union

from networkx import DiGraph

from amino import List, Path, do, Either, Try, Do, Maybe, Regex, Nil, Nothing, ADT, Just, Dat
from amino.util.numeric import parse_int
from amino.logging import module_log

from myo.output.data.output import OutputLine, OutputEvent, Location
from myo.output.parser.base import EdgeData, Parser

log = module_log()


class ScalaLine(ADT['ScalaLine']):
    pass


class FileLine(ScalaLine):

    @staticmethod
    @do(Either[str, 'FileLine'])
    def cons(
            path: Union[str, Path],
            line: Union[str, int],
            col: Union[str, int]=None,
            error: str='',
            tag: str='',
    ) -> Do:
        path_p = yield Try(Path, path)
        line_i = yield parse_int(line)
        col_i = yield parse_int(0 if col is None else col)
        return FileLine(path_p, line_i, col_i, error, tag)

    def __init__(self, path: Path, line: int, col: int, error: str, tag: str) -> None:
        self.path = path
        self.line = line
        self.col = col
        self.error = error
        self.tag = tag


class CodeLine(ScalaLine):

    @staticmethod
    def cons(code: str, tag: str='') -> 'CodeLine':
        return CodeLine(code, tag)

    def __init__(self, code: str, tag: str) -> None:
        self.code = code
        self.tag = tag


class ColLine(ScalaLine):

    @staticmethod
    def cons(ws: str, tag: str='') -> 'CodeLine':
        return ColLine(len(ws), tag)

    def __init__(self, col: int, tag: str) -> None:
        self.col = col
        self.tag = tag


_msg_type = '\[(?P<tag>\w+)\] '
file_edge = EdgeData(
    regex=Regex(f'^{_msg_type}\s*(?P<path>[^:]+):(?P<line>\d+):((?P<col>\d+):)?\s*(?P<error>.*?);?$'),
    cons_output_line=FileLine.cons,
)
code_edge = EdgeData.strict(
    regex=Regex(f'^{_msg_type}(?P<code>\s*.+)'),
    cons_output_line=CodeLine.cons,
)
col_edge = EdgeData.strict(
    regex=Regex(f'^{_msg_type}(?P<ws>\s*)\^\s*'),
    cons_output_line=ColLine.cons,
)


class ScalaEvent(Dat['ScalaEvent']):

    @staticmethod
    def cons(
            file: OutputLine[FileLine],
            code: List[OutputLine[CodeLine]]=Nil,
            col: Maybe[OutputLine[ColLine]]=Nothing,
    ) -> 'ScalaOutputEvent':
        return ScalaEvent(file, code, col)

    def __init__(
            self,
            file: OutputLine[FileLine],
            code: List[OutputLine[CodeLine]],
            col: Maybe[OutputLine[ColLine]],
    ) -> None:
        self.file = file
        self.code = code
        self.col = col


def scala_graph() -> DiGraph:
    g = DiGraph()
    g.add_edge('start', 'file', data=file_edge)
    g.add_edge('file', 'error', data=code_edge)
    g.add_edge('error', 'error', data=code_edge)
    g.add_edge('error', 'col', data=col_edge, weight=1)
    return g


@do(Maybe[OutputEvent[ScalaLine, ScalaEvent]])
def scala_event(lines: List[OutputLine[ScalaLine]]) -> Do:
    col = lines.find(lambda a: isinstance(a.meta, ColLine))
    file = yield lines.find(lambda a: isinstance(a.meta, FileLine))
    code = lines.filter(lambda a: isinstance(a.meta, CodeLine))
    location = Location(file.meta.path, file.meta.line, col.map(lambda a: a.meta.col).get_or_strict(0))
    return OutputEvent.cons(ScalaEvent(file, code, col), lines, Just(location))


def scala_events(lines: List[OutputLine[ScalaLine]]) -> List[OutputEvent[ScalaLine, ScalaEvent]]:
    return scala_event(lines).to_list


scala_parser = Parser(scala_graph(), scala_events)

__all__ = ('scala_parser',)
