from typing import TypeVar, Callable, Tuple

from amino import do, _, Do, List, __, Just, Boolean, IO, Either, Left, Right, Lists
from amino.boolean import true, false
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.case import Case
from amino.state import State

from ribosome.nvim.io.state import NS
from ribosome.nvim.scratch import show_in_scratch_buffer, CreateScratchBufferOptions, ScratchBuffer
from ribosome.compute.api import prog
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.ui import (window_line, focus_window, edit_file, set_local_cursor, set_line, window_buffer_name,
                                  close_buffer)
from ribosome.nvim.io.api import N
from ribosome.components.internal.mapping import activate_mapping
from ribosome.data.mapping import Mapping
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.data import CommandData, OutputData
from myo.output.data.output import OutputLine, Location, OutputEvent
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import auto_jump
from myo.output.data.report import ReportLine, format_report, ParseReport, PlainReportLine, EventReportLine, event_index
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import Reporter

log = module_log()
A = TypeVar('A')
B = TypeVar('B')
D = TypeVar('D')
jump_mapping = Mapping.cons('output_jump', '<cr>', true)
quit_mapping = Mapping.cons('output_quit', 'q', true)
prev_mapping = Mapping.cons('output_prev', '<m-->', false)
next_mapping = Mapping.cons('output_next', '<m-=>', false)


def output_data() -> NS[CommandData, OutputData]:
    return NS.inspect(_.output)


def scratch_buffer() -> NS[CommandData, ScratchBuffer]:
    return NS.inspect_either(__.output.scratch.to_either('no scratch buffer set'))


def output_entry_at(index: int) -> NS[CommandData, OutputLine]:
    return NS.inspect_maybe(__.output.locations.lift(index), lambda: f'invalid output entry index {index}')


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
        yield edit_file(location.path) if current_file != location.path else N.unit
        yield set_local_cursor(location.coords)
    yield N.unit


@do(NS[CommandData, None])
def select_event(index: int, jump: Boolean) -> Do:
    yield NS.modify(__.set.current(index)).zoom(lens.output)
    line = yield inspect_report_line_number_by_event_index(index)
    scratch = yield scratch_buffer()
    yield NS.lift(set_line(scratch.ui.window, line + 1))
    yield NS.modify(__.set.current(index)).zoom(lens.output)
    if jump:
        location = yield inspect_line_location(line)
        yield NS.lift(jump_to_location(scratch, location))


def event_report(index: int, event: OutputEvent[A, B], lines: List[str]) -> List[ReportLine]:
    return (
        (event.head / PlainReportLine) +
        (lines.map(lambda a: EventReportLine(a, index, event.location)))
    )


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
def render_parse_result(output: ParsedOutput[A, B]) -> Do:
    log.debug(f'rendering parse result')
    report = yield parse_report(output)
    scratch = yield NS.lift(show_in_scratch_buffer(format_report(report), CreateScratchBufferOptions.cons()))
    yield Ribo.modify_comp(lens.output.modify(__.copy(report=report, scratch=Just(scratch))))
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.state)
    jump = yield Ribo.setting(auto_jump)
    first_error = yield output.handlers.first_error(output)
    yield Ribo.zoom_comp(select_event(first_error, jump))


@prog.comp
@do(NS[CommandData, None])
def current_event_jump() -> Do:
    scratch = yield scratch_buffer()
    line = yield NS.lift(window_line(scratch.ui.window))
    location = yield inspect_line_location(line)
    yield NS.lift(jump_to_location(scratch, location))


@prog.comp
@do(NS[CommandData, None])
def quit_output() -> Do:
    scratch = yield scratch_buffer()
    yield NS.lift(close_buffer(scratch.buffer))


@prog
@do(NS[CommandRibosome, None])
def prev_event() -> Do:
    current = yield Ribo.inspect_comp(_.output.current)
    jump = yield Ribo.setting(auto_jump)
    if current > 0:
        yield Ribo.zoom_comp(select_event(current - 1, jump))


@prog
@do(NS[CommandRibosome, None])
def next_event() -> Do:
    current = yield Ribo.inspect_comp(_.output.current)
    count = yield Ribo.inspect_comp(_.output.report.event_indexes.length)
    if current < count - 1:
        jump = yield Ribo.setting(auto_jump)
        yield Ribo.zoom_comp(select_event(current + 1, jump))


__all__ = ('render_parse_result', 'current_event_jump', 'quit_output', 'prev_event', 'next_event')
