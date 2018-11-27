
from amino import List, do, Do, Nil
from amino.logging import module_log

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.data.output import OutputEvent, Location
from myo.components.command.compute.parse_handlers import PathFormatter
from myo.output.data.report import DisplayLine, PlainDisplayLine
from myo.output.parser.haskell import HaskellEvent, HaskellLine

from ribosome.nvim.io.state import NS

log = module_log()


@do(NS[CommandRibosome, List[DisplayLine]])
def format_location(location: Location, path_formatter: PathFormatter) -> Do:
    path = yield path_formatter(location.path)
    return List(PlainDisplayLine(f'{path}  {location.line + 1}'))


@do(NS[CommandRibosome, List[DisplayLine]])
def haskell_report(path_formatter: PathFormatter, output: OutputEvent[HaskellLine, HaskellEvent]) -> Do:
    info = output.meta.info.map(lambda a: a.meta.message).indent(2).map(PlainDisplayLine)
    location = yield output.location.map(lambda a: format_location(a, path_formatter)).get_or(NS.pure, Nil)
    return location + info


__all__ = ('haskell_report',)
