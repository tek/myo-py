from typing import TypeVar

from amino import do, _, Do, List, __, Just, Boolean, IO
from amino.boolean import true
from amino.lenses.lens import lens

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
from myo.output.data import ParseResult, OutputEntry, OutputLine, Location
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import auto_jump

D = TypeVar('D')
jump_mapping = Mapping.cons('output_jump', '<cr>', true)
quit_mapping = Mapping.cons('output_quit', 'q', true)
prev_mapping = Mapping.cons('output_prev', '<m-->', true)
next_mapping = Mapping.cons('output_next', '<m-=>', true)


def output_data() -> NS[CommandData, OutputData]:
    return NS.inspect(_.output)


def scratch_buffer() -> NS[CommandData, ScratchBuffer]:
    return NS.inspect_either(__.output.scratch.to_either('no scratch buffer set'))


def output_entry_at(index: int) -> NS[CommandData, OutputEntry]:
    return NS.inspect_maybe(__.output.locations.lift(index), lambda: f'invalid output entry index {index}')


def output_line_for(entry: OutputEntry) -> NS[CommandData, OutputLine]:
    return (
        NS.inspect_maybe(__.index_where(__.entry.contains(entry)), lambda: f'no matching line for location {entry}')
        .zoom(lens.output.lines)
    )


@do(NvimIO[None])
def jump_to_location(scratch: ScratchBuffer, location: Location) -> Do:
    window = scratch.ui.previous
    yield focus_window(window)
    current_file = yield window_buffer_name(window)
    location_exists = yield N.from_io(IO.delay(location.file_path.exists))
    if location_exists:
        yield edit_file(location.file_path) if current_file != location.file_path else N.pure(None)
        yield set_local_cursor(location.coords)
    yield N.unit


# FIXME entries can be identical, need uuid for lookup; or implement better model
@do(NS[CommandData, None])
def select_entry(index: int, jump: Boolean) -> Do:
    yield NS.modify(__.set.current(index)).zoom(lens.output)
    location = yield output_entry_at(index)
    line = yield output_line_for(location)
    scratch = yield scratch_buffer()
    yield NS.lift(set_line(scratch.ui.window, line + 1))
    yield NS.modify(__.set.current(index)).zoom(lens.output)
    if jump:
        yield NS.lift(jump_to_location(scratch, location))


@do(NS[CommandRibosome, None])
def render_parse_result(result: ParseResult) -> Do:
    lines = result.lines
    locations = result.locations
    scratch = yield NS.lift(show_in_scratch_buffer(lines / _.formatted, CreateScratchBufferOptions.cons()))
    yield Ribo.modify_comp(lens.output.modify(__.copy(lines=lines, locations=locations, scratch=Just(scratch))))
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.state)
    jump = yield Ribo.setting(auto_jump)
    yield Ribo.zoom_comp(select_entry(0, jump))


@prog.comp
@do(NS[CommandData, None])
def current_entry_jump() -> Do:
    output = yield output_data()
    scratch = yield scratch_buffer()
    line = yield NS.lift(window_line(scratch.ui.window))
    location = yield NS.from_maybe(output.lines.lift(line) / _.target, 'current line has no location')
    yield NS.lift(jump_to_location(scratch, location))


@prog.comp
@do(NS[CommandData, None])
def quit_output() -> Do:
    scratch = yield scratch_buffer()
    yield NS.lift(close_buffer(scratch.buffer))


@prog
@do(NS[CommandRibosome, None])
def prev_entry() -> Do:
    current = yield Ribo.inspect_comp(_.output.current)
    jump = yield Ribo.setting(auto_jump)
    if current > 0:
        yield Ribo.zoom_comp(select_entry(current - 1, jump))


@prog
@do(NS[CommandRibosome, None])
def next_entry() -> Do:
    current = yield Ribo.inspect_comp(_.output.current)
    count = yield Ribo.inspect_comp(_.output.locations.length)
    if current < count - 1:
        jump = yield Ribo.setting(auto_jump)
        yield Ribo.zoom_comp(select_entry(current + 1, jump))


__all__ = ('render_parse_result', 'current_entry_jump', 'quit_output', 'prev_entry', 'next_entry')
