from amino import List, Nil, do, Do
from amino.case import Case

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.parser.python import PythonLine, PythonEvent, StackFrameEvent, ErrorEvent, FileLine
from myo.output.data.output import OutputEvent, Location, OutputLine
from myo.components.command.compute.parse_handlers import PathFormatter
from myo.output.data.report import DisplayLine, PlainDisplayLine

from ribosome.nvim.io.state import NS


@do(NS[CommandRibosome, List[DisplayLine]])
def format_location(file: OutputLine[FileLine], location: Location, path_formatter: PathFormatter) -> Do:
    fun = file.meta.fun.map(lambda a: f' {a}').get_or_strict('')
    path = yield path_formatter(location.path)
    return List(PlainDisplayLine(f'{path}  {location.line}{fun}'))


class python_report_event(Case[PythonEvent, NS[CommandRibosome, List[DisplayLine]]], alg=PythonEvent):

    def __init__(self, path_formatter: PathFormatter, event: OutputEvent[PythonLine, PythonEvent]) -> None:
        self.path_formatter = path_formatter
        self.event = event

    @do(NS[CommandRibosome, List[DisplayLine]])
    def stack_frame(self, event: StackFrameEvent) -> Do:
        loc_line = yield (
            self.event.location
            .map(lambda a: format_location(event.file, a, self.path_formatter))
            .get_or_strict(NS.pure(Nil))
        )
        code_line = event.code.map(lambda a: PlainDisplayLine(a.text)).to_list
        return loc_line + code_line

    def error(self, event: ErrorEvent) -> NS[CommandRibosome, List[DisplayLine]]:
        return NS.pure(List(PlainDisplayLine(event.line.text)))


def python_report(
        path_formatter: PathFormatter,
        output: OutputEvent[PythonLine, PythonEvent]
) -> NS[CommandRibosome, List[DisplayLine]]:
    return python_report_event(path_formatter, output)(output.meta)


__all__ = ('python_report',)
