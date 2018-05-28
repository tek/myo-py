from typing import TypeVar, Callable

from amino import do, _, Do, List, __, Just, Boolean, IO, Either, Left, Right
from amino.boolean import true
from amino.lenses.lens import lens
from amino.logging import module_log
from amino.case import Case

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
from myo.output.data.output import ParseResult, OutputLine, Location, OutputEvent
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import auto_jump
from myo.output.data.report import (ReportLine, parse_report, format_report, ParseReport, PlainReportLine,
                                    EventReportLine)

log = module_log()
D = TypeVar('D')
jump_mapping = Mapping.cons('output_jump', '<cr>', true)
quit_mapping = Mapping.cons('output_quit', 'q', true)
prev_mapping = Mapping.cons('output_prev', '<m-->', true)
next_mapping = Mapping.cons('output_next', '<m-=>', true)


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


# FIXME lines can be identical, need uuid for lookup; or implement better model
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


@do(NS[CommandRibosome, None])
def render_parse_result(events: List[OutputEvent]) -> Do:
    report = parse_report(events)
    scratch = yield NS.lift(show_in_scratch_buffer(format_report(report), CreateScratchBufferOptions.cons()))
    yield Ribo.modify_comp(lens.output.modify(__.copy(report=report, scratch=Just(scratch))))
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.state)
    jump = yield Ribo.setting(auto_jump)
    yield Ribo.zoom_comp(select_event(0, jump))


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
