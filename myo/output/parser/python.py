from typing import Union

from networkx import DiGraph

from amino import List, Just, Maybe, Path, Regex, Nothing, do, Either, Do, Try, ADT, Nil, Dat
from amino.util.numeric import parse_int
from amino.case import Case

from myo.output.data.output import OutputLine, OutputEvent, Location
from myo.output.parser.base import EdgeData, Parser


class PythonLine(ADT['PythonLine']):
    pass


class CodeLine(PythonLine):

    def __init__(self, code: str) -> None:
        self.code = code


class FileLine(PythonLine):

    @staticmethod
    @do(Either[str, 'FileLine'])
    def cons(
            path: Union[str, Path],
            line: Union[str, int],
            fun: str=None,
    ) -> Do:
        path_p = yield Try(Path, path)
        line_i = yield parse_int(line)
        return FileLine(path_p, line_i, Maybe.optional(fun))

    def __init__(self, path: Path, line: int, fun: Maybe[str]) -> None:
        self.path = path
        self.line = line
        self.fun = fun


class ErrorLine(PythonLine):

    def __init__(self, error: str, exc: str) -> None:
        self.error = error
        self.exc = exc


class ColLine(PythonLine):

    @staticmethod
    def whitespace(ws: str) -> 'ColLine':
        return ColLine(len(ws))

    def __init__(self, col: int) -> None:
        self.col = col


file_edge = EdgeData(
    regex=Regex('\s*File "(?P<path>.+)", line (?P<line>\d+)(?:, in (?P<fun>\S+))?'),
    cons_output_line=FileLine.cons
)
code_edge = EdgeData.strict(regex=Regex('^\s*(?P<code>.+)'), cons_output_line=CodeLine)
error_edge = EdgeData.strict(regex=Regex('^\s*(?P<exc>\S+): (?P<error>.+)'), cons_output_line=ErrorLine)
col_edge = EdgeData.strict(regex=Regex('^\s*(?P<ws>\s+)\^'), cons_output_line=ColLine.whitespace)


def python_graph() -> DiGraph:
    g = DiGraph()
    g.add_edge('start', 'file', data=file_edge)
    g.add_edge('file', 'code', data=code_edge)
    g.add_edge('code', 'file', data=file_edge)
    g.add_edge('code', 'error', data=error_edge)
    g.add_edge('code', 'col', data=col_edge)
    g.add_edge('col', 'error', data=error_edge)
    return g


class EventData(Dat['EventData']):

    @staticmethod
    def cons(
            output: List[OutputEvent]=Nil,
            file: Maybe[FileLine]=Nothing,
            code: Maybe[CodeLine]=Nothing,
            col: Maybe[ColLine]=Nothing,
    ) -> 'EventData':
        return EventData(
            output,
            file,
            code,
            col,
        )

    def __init__(
            self,
            output: List[OutputEvent],
            file: Maybe[FileLine],
            code: Maybe[CodeLine],
            col: Maybe[ColLine],
    ) -> None:
        self.output = output
        self.file = file
        self.code = code
        self.col = col


class PythonEvent(ADT['PythonEvent']):
    pass


class StackFrameEvent(PythonEvent):

    def __init__(self, file: OutputLine[FileLine], code: Maybe[OutputLine[CodeLine]]) -> None:
        self.file = file
        self.code = code


class ErrorEvent(PythonEvent):

    def __init__(self, line: OutputLine[PythonLine]) -> None:
        self.line = line


def stack_frame_event(
        file: OutputLine[FileLine],
        code: Maybe[OutputLine[CodeLine]],
        col: Maybe[OutputLine[ColLine]],
) -> OutputEvent:
    lines = List(file).cat_m(code)
    location = Location(file.meta.path, file.meta.line, col.map(lambda a: a.meta.col).get_or_strict(0))
    return OutputEvent.cons(StackFrameEvent(file, code), lines, Just(location))


def push_event(data: EventData) -> EventData:
    event = data.file.map(lambda a: stack_frame_event(a, data.code, data.col))
    new = event.cata(data.append1.output, data)
    return EventData.cons(output=new.output)


class update_event_data(Case[PythonLine, EventData], alg=PythonLine):

    def __init__(self, current: EventData, line: OutputLine[PythonLine]) -> None:
        self.current = current
        self.line = line

    def error(self, meta: ErrorLine) -> EventData:
        return push_event(self.current).append1.output(OutputEvent.cons(ErrorEvent(self.line), List(self.line)))

    def code(self, meta: CodeLine) -> EventData:
        return self.current.set.code(Just(self.line))

    def col(self, meta: ColLine) -> EventData:
        return self.current.set.col(Just(self.line))

    def file(self, meta: FileLine) -> EventData:
        return push_event(self.current).set.file(Just(self.line))


def python_events(lines: List[OutputLine[PythonLine]]) -> List[OutputEvent[PythonLine, PythonEvent]]:
    data = lines.fold_left(EventData.cons())(lambda z, a: update_event_data(z, a)(a.meta))
    return push_event(data).output


python_parser = Parser(python_graph(), python_events)

__all__ = ('python_parser',)
