from typing import Union

from networkx import DiGraph

from amino import List, _, Path, do, Either, Try, Do, Maybe, Regex, Nil, Nothing, ADT, Just
from amino.util.numeric import parse_int

from myo.output.data.output import OutputLine, OutputEvent, Location
from myo.output.parser.base import EdgeData, Parser


class ScalaLine(ADT['ScalaLine']):
    pass


class FileLine(ScalaLine):

    @staticmethod
    @do(Either[str, 'FileLine'])
    def cons(
            path: Union[str, Path],
            line: Union[str, int],
            col: Union[str, int]=0,
            fun: str=None,
            error: str='',
            tag: str='',
    ) -> Do:
        path_p = yield Try(Path, path)
        line_i = yield parse_int(line)
        col_i = yield parse_int(col)
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
    regex=Regex(f'^{_msg_type}\s*(?P<path>[^:]+):(?P<line>\d+):\s*(?P<error>.*?);?$'),
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


class ScalaOutputEvent(OutputEvent):

    @staticmethod
    def cons(
            file: FileLine,
            head: List[str]=Nil,
            lines: List[OutputLine[ScalaLine]]=Nil,
            col: Maybe[OutputLine[ColLine]]=Nothing,
    ) -> 'ScalaOutputEvent':
        return ScalaOutputEvent(file, head, lines, col)

    def __init__(
            self,
            file: FileLine,
            head: List[str],
            lines: List[OutputLine[ScalaLine]],
            col: Maybe[OutputLine[ColLine]],
    ) -> None:
        self.file = file
        self.head = head
        self.lines = lines
        self.col = col

    @property
    def location(self):
        return self.file

    @property
    def file_path(self):
        return self.file.file_path

    @property
    def coords(self):
        return self.file.line, self.col / _.col | 1

    @property
    def code(self):
        return self.lines.filter_type(CodeLine)

    @property
    def locations(self):
        return List(self)


def scala_graph() -> DiGraph:
    g = DiGraph()
    g.add_edge('start', 'file', data=file_edge)
    g.add_edge('file', 'error', data=code_edge)
    g.add_edge('error', 'error', data=code_edge)
    g.add_edge('error', 'col', data=col_edge, weight=1)
    return g


@do(Maybe[OutputEvent])
def scala_event(lines: List[OutputLine[ScalaLine]]) -> Do:
    col = lines.find(lambda a: isinstance(a.meta, ColLine))
    file = yield lines.find(lambda a: isinstance(a.meta, FileLine))
    location = Location(file.meta.path, file.meta.line, col.map(lambda a: a.meta.col).get_or_strict(0))
    return OutputEvent.cons(lines, Just(location), Nil)


def scala_events(lines: List[OutputLine[ScalaLine]]) -> List[OutputEvent[ScalaLine]]:
    return scala_event(lines).to_list


scala_parser = Parser(scala_graph(), scala_events)

__all__ = ('scala_parser',)
