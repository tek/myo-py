from amino import List, do, Do, Nil, Maybe

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.data.output import OutputEvent, Location, OutputLine
from myo.components.command.compute.parse_handlers import PathFormatter
from myo.output.data.report import DisplayLine, PlainDisplayLine
from myo.output.parser.scala import ScalaEvent, ScalaLine, ColLine

from ribosome.nvim.io.state import NS

col_marker = '†'


@do(NS[CommandRibosome, List[DisplayLine]])
def format_location(location: Location, path_formatter: PathFormatter) -> Do:
    path = yield path_formatter(location.path)
    return List(PlainDisplayLine(f'{path}  {location.line}'))


def inject_col_marker(code: str, col_line: Maybe[OutputLine[ColLine]]) -> str:
    col = col_line.map(lambda a: a.meta.col).get_or_strict(0)
    return f'{code[:col]}{col_marker}{code[col:]}'


@do(NS[CommandRibosome, List[DisplayLine]])
def scala_report(path_formatter: PathFormatter, output: OutputEvent[ScalaLine, ScalaEvent]) -> Do:
    code = (
        output.meta.code
        .map(lambda a: inject_col_marker(a.meta.code, output.meta.col))
        .indent(2)
        .map(PlainDisplayLine)
    )
    location = yield output.location.map(lambda a: format_location(a, path_formatter)).get_or(NS.pure, Nil)
    error = PlainDisplayLine(output.meta.file.meta.error)
    return location.cat(error) + code


__all__ = ('scala_report',)
