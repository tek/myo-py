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


class InfoLine(ScalaLine):

    @staticmethod
    def cons(message: str, ws: str='', tag: str='') -> 'InfoLine':
        return InfoLine(message, len(ws), tag)

    def __init__(self, message: str, indent: int, tag: str) -> None:
        self.message = message
        self.indent = indent
        self.tag = tag


class CodeLine(ScalaLine):

    def __init__(self, code: str, indent: int, tag: str) -> None:
        self.code = code
        self.indent = indent
        self.tag = tag


class ColLine(ScalaLine):

    @staticmethod
    def cons(ws: str, tag: str='') -> 'ColLine':
        return ColLine(len(ws), tag)

    def __init__(self, col: int, tag: str) -> None:
        self.col = col
        self.tag = tag


_msg_type = '\[(?P<tag>\w+)\] '
file_edge: EdgeData[FileLine] = EdgeData(
    regex=Regex(f'^{_msg_type}\s*(?P<path>[^:]+):(?P<line>\d+):((?P<col>\d+):)?\s*(?P<error>.*?);?$'),
    cons_output_line=FileLine.cons,
)
info_edge = EdgeData.strict(
    regex=Regex(f'^{_msg_type}(?P<ws>\s*)(?P<message>\s*.+)'),
    cons_output_line=InfoLine.cons,
)
col_edge = EdgeData.strict(
    regex=Regex(f'^{_msg_type}(?P<ws>\s*)\^\s*'),
    cons_output_line=ColLine.cons,
)


class ScalaEvent(Dat['ScalaEvent']):

    @staticmethod
    def cons(
            file: OutputLine[FileLine],
            info: List[OutputLine[InfoLine]]=Nil,
            code: Maybe[OutputLine[CodeLine]]=Nothing,
            col: Maybe[OutputLine[ColLine]]=Nothing,
    ) -> 'ScalaOutputEvent':
        return ScalaEvent(file, info, code, col)

    def __init__(
            self,
            file: OutputLine[FileLine],
            info: List[OutputLine[InfoLine]],
            code: Maybe[OutputLine[CodeLine]],
            col: Maybe[OutputLine[ColLine]],
    ) -> None:
        self.file = file
        self.info = info
        self.code = code
        self.col = col


def scala_graph() -> DiGraph:
    g = DiGraph()
    g.add_edge('start', 'file', data=file_edge)
    g.add_edge('file', 'info', data=info_edge)
    g.add_edge('info', 'info', data=info_edge)
    g.add_edge('info', 'col', data=col_edge, weight=1)
    return g


@do(Maybe[OutputEvent[ScalaLine, ScalaEvent]])
def scala_event(lines: List[OutputLine[ScalaLine]]) -> Do:
    col = lines.find(lambda a: isinstance(a.meta, ColLine))
    file = yield lines.find(lambda a: isinstance(a.meta, FileLine))
    info = lines.filter(lambda a: isinstance(a.meta, InfoLine))
    code, infos = (
        info.detach_last
        .map2(lambda c, e: (Just(OutputLine(c.text, CodeLine(c.meta.message, c.meta.indent, c.meta.tag), c.indent)), e))
        .get_or_strict((Nothing, Nil))
    )
    location = Location(file.meta.path, file.meta.line, col.map(lambda a: a.meta.col).get_or_strict(0))
    return OutputEvent.cons(ScalaEvent(file, infos, code, col), lines, Just(location))


def scala_events(lines: List[OutputLine[ScalaLine]]) -> List[OutputEvent[ScalaLine, ScalaEvent]]:
    return scala_event(lines).to_list


scala_parser = Parser(scala_graph(), scala_events)

__all__ = ('scala_parser',)
