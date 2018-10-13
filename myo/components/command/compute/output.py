from typing import TypeVar, Callable, Tuple

from amino import do, Do, List, Just, Boolean, IO, Either, Left, Lists, Nothing
from amino.boolean import true, false
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.case import Case
from amino.state import State

from ribosome.nvim.io.state import NS
from ribosome.nvim.scratch import show_in_scratch_buffer_default, ScratchBuffer
from ribosome.compute.api import prog
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.ui import (window_line, focus_window, edit_file, set_local_cursor, set_line, window_buffer_name,
                                  close_buffer, window_number, close_window)
from ribosome.nvim.io.api import N
from ribosome.components.internal.mapping import activate_mapping
from ribosome.data.mapping import Mapping
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.syntax.cmd import syntax_item_cmd, highlight_cmd, hi_link_cmd
from ribosome.nvim.api.command import nvim_atomic_commands, nvim_command
from ribosome.nvim.api.util import format_windo
from ribosome import ribo_log

from myo.components.command.data import CommandData, OutputData
from myo.output.data.output import Location, OutputEvent
from myo.components.command.compute.tpe import CommandRibosome
from myo.config.settings import auto_jump
from myo.output.data.report import (ReportLine, format_report, ParseReport, PlainReportLine, EventReportLine,
                                    event_index, DisplayLine)
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import Reporter, SyntaxCons

log = module_log()
A = TypeVar('A')
B = TypeVar('B')
D = TypeVar('D')
jump_mapping = Mapping.cons('output_jump', '<cr>', true)
quit_mapping = Mapping.cons('output_quit', 'q', true)
prev_mapping = Mapping.cons('output_prev', '<m-->', false)
next_mapping = Mapping.cons('output_next', '<m-=>', false)


def output_data() -> NS[CommandData, OutputData]:
    return NS.inspect(lambda a: a.output)


def scratch_buffer() -> NS[CommandData, ScratchBuffer]:
    return NS.inspect_either(lambda a: a.output.scratch.to_either('no scratch buffer set'))


def report_line_number(event: int) -> Callable[[ParseReport], Either[str, int]]:
    err = lambda: f'no matching line for event {event}'
    def report_line_number(report: ParseReport) -> Either[str, int]:
        return report.event_indexes.lift(event).to_either_f(err)
    return report_line_number


@do(NS[CommandData, int])
def inspect_report_line_number_by_event_index(index: int) -> Do:
    yield (
        NS.inspect_either(report_line_number(index))
        .zoom(lens.output.report)
    )


@do(NS[CommandData, int])
def line_event_index(line: int) -> Do:
    indexes = yield NS.inspect(lambda a: a.output.report.event_indexes)
    return indexes.index_where(lambda a: a > line + 1).get_or_strict(len(indexes)) - 1


no_associated_location = 'no location associated with this event'


class report_line_location(Case[ReportLine, Either[str, Location]], alg=ReportLine):

    def plain(self, line: PlainReportLine) -> Either[str, Location]:
        return Left(no_associated_location)

    def event(self, line: EventReportLine) -> Either[str, Location]:
        return line.location.to_either(no_associated_location)


def line_location(line: int) -> Callable[[ParseReport], Either[str, Location]]:
    @do(Either[str, Location])
    def report_line_number(report: ParseReport) -> Do:
        report_line = yield report.lines.lift(line).to_either(lambda: f'invalid report line index {line}')
        yield report_line_location.match(report_line)
    return report_line_number


@do(NS[CommandData, Location])
def inspect_line_location(line: int) -> Do:
    yield NS.inspect_either(line_location(line)).zoom(lens.output.report)


@do(NvimIO[None])
def jump_to_location(scratch: ScratchBuffer, location: Location) -> Do:
    window = scratch.ui.previous
    yield focus_window(window)
    current_file = yield window_buffer_name(window)
    location_exists = yield N.from_io(IO.delay(location.path.exists))
    if location_exists:
        yield edit_file(location.path) if current_file != str(location.path) else N.unit
        yield set_local_cursor(location.coords)
        yield nvim_command('normal! zvzz')
    yield N.unit


def store_event_index(index: int) -> NS[CommandData, None]:
    return NS.s(CommandData).modify(lambda a: a.set.current(index)).zoom(lens.output)


@do(NS[CommandData, None])
def select_event(index: int, jump: Boolean) -> Do:
    yield store_event_index(index)
    line = yield inspect_report_line_number_by_event_index(index)
    scratch = yield scratch_buffer()
    yield NS.lift(set_line(scratch.ui.window, line))
    if jump:
        location = yield inspect_line_location(line)
        yield NS.lift(jump_to_location(scratch, location))


@do(NS[CommandData, None])
def select_line_event(line: int) -> Do:
    index = yield line_event_index(line)
    yield store_event_index(index)


def event_report(index: int, event: OutputEvent[A, B], lines: List[DisplayLine]) -> List[ReportLine]:
    return lines.map(lambda a: EventReportLine(a, index, event.location))


@do(NS[CommandRibosome, List[List[ReportLine]]])
def events_report(output: ParsedOutput[A, B], reporter: Reporter) -> Do:
    reports = yield output.filtered.traverse(lambda a: reporter(output.handlers.path_formatter, a), NS)
    return Lists.range(len(reports)).zip(output.filtered, reports).map3(event_report)


@do(NS[CommandRibosome, ParseReport])
def parse_report(output: ParsedOutput[A, B]) -> Do:
    events_lines = yield events_report(output, output.handlers.reporter)
    lines = events_lines.join
    event_indexes = events_lines.traverse(event_index, State).run_a(0).value
    return ParseReport(lines, event_indexes)


@do(NS[CommandRibosome, None])
def setup_syntax(cons: SyntaxCons, window: int) -> Do:
    syntax = yield cons()
    cmds = (
        syntax.syntax.map(syntax_item_cmd.match) +
        syntax.highlight.map(highlight_cmd) +
        syntax.links.map(hi_link_cmd) +
        List('setlocal conceallevel=2')
    )
    win_cmds = cmds.map(lambda a: format_windo(a, window, Nothing))
    yield NS.lift(nvim_atomic_commands(win_cmds))


@do(NvimIO[None])
def close_scratch_buffer(scratch: ScratchBuffer) -> Do:
    yield N.ignore_failure(close_window(scratch.ui.window))
    yield N.ignore_failure(close_buffer(scratch.buffer))


@do(NS[CommandRibosome, None])
def terminate_scratch() -> Do:
    scratch = yield Ribo.inspect_comp(lambda a: a.output.scratch)
    yield NS.lift(scratch.cata(close_scratch_buffer, N.unit))


@do(NS[CommandRibosome, None])
def empty_report() -> Do:
    ribo_log.error('no events in command output')
    yield NS.unit


@do(NS[CommandRibosome, None])
def render_report(output: ParsedOutput[A, B], report: ParseReport) -> Do:
    yield terminate_scratch()
    scratch = yield NS.lift(show_in_scratch_buffer_default(format_report(report), max_height=Just(.3)))
    scratch_number = yield NS.lift(window_number(scratch.ui.window))
    yield Ribo.modify_comp(lens.output.modify(lambda a: a.copy(report=report, scratch=Just(scratch))))
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.state)
    yield setup_syntax(output.handlers.syntax, scratch_number)
    jump = yield Ribo.setting(auto_jump)
    first_error = yield output.handlers.first_error(output.filtered)
    yield Ribo.zoom_comp(select_event(first_error, jump))


@do(NS[CommandRibosome, None])
def render_parse_result(output: ParsedOutput[A, B]) -> Do:
    log.debug(f'rendering parse result')
    report = yield parse_report(output)
    yield empty_report() if report.event_indexes.empty else render_report(output, report)


@do(NS[CommandRibosome, Tuple[ScratchBuffer, int]])
def select_cursor_event() -> Do:
    scratch = yield Ribo.zoom_comp(scratch_buffer())
    line = yield NS.lift(window_line(scratch.ui.window))
    yield Ribo.zoom_comp(select_line_event(line))
    return scratch, line


@prog
@do(NS[CommandRibosome, None])
def current_event_jump() -> Do:
    scratch, line = yield select_cursor_event()
    location = yield Ribo.zoom_comp(inspect_line_location(line))
    yield NS.lift(jump_to_location(scratch, location))


@prog.comp
@do(NS[CommandData, None])
def quit_output() -> Do:
    scratch = yield scratch_buffer()
    yield NS.lift(close_buffer(scratch.buffer))


@prog
@do(NS[CommandRibosome, None])
def prev_event() -> Do:
    current = yield Ribo.inspect_comp(lambda a: a.output.current)
    if current > 0:
        jump = yield Ribo.setting(auto_jump)
        yield Ribo.zoom_comp(select_event(current - 1, jump))


@prog
@do(NS[CommandRibosome, None])
def next_event() -> Do:
    current = yield Ribo.inspect_comp(lambda a: a.output.current)
    count = yield Ribo.inspect_comp(lambda a: a.output.report.event_indexes.length)
    if current < count - 1:
        jump = yield Ribo.setting(auto_jump)
        yield Ribo.zoom_comp(select_event(current + 1, jump))


__all__ = ('render_parse_result', 'current_event_jump', 'quit_output', 'prev_event', 'next_event')
