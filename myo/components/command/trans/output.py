from typing import TypeVar

from amino import do, _, Do, List, __, Just, Boolean, IO
from amino.boolean import true
from amino.lenses.lens import lens

from ribosome.nvim.io import NS
from ribosome.nvim.scratch import show_in_scratch_buffer, CreateScratchBufferOptions, ScratchBuffer
from ribosome.dispatch.component import ComponentData
from ribosome.trans.api import trans
from ribosome.trans.mapping import activate_mapping
from ribosome.dispatch.mapping import Mapping
from ribosome.nvim.api import (window_line, focus_window, edit_file, set_local_cursor, set_line, window_buffer_name,
                               close_buffer)
from ribosome.nvim import NvimIO
from ribosome.config.config import Resources

from myo.components.command.data import CommandData, OutputData
from myo.output.data import ParseResult, OutputEntry, OutputLine, Location
from myo.config.plugin_state import MyoPluginState
from myo.env import Env
from myo.settings import setting, MyoSettings
from myo.config.component import MyoComponent

D = TypeVar('D')
jump_mapping = Mapping.cons('<cr>', true)
quit_mapping = Mapping.cons('q', true)
prev_mapping = Mapping.cons('<m-->', true)
next_mapping = Mapping.cons('<m-=>', true)


def output_data() -> NS[ComponentData[D, CommandData], OutputData]:
    return NS.inspect(_.comp.output)


def scratch_buffer() -> NS[ComponentData[D, CommandData], ScratchBuffer]:
    return NS.inspect_either(__.to_either('no scratch buffer set')).zoom(lens.comp.output.scratch)


def output_entry_at(index: int) -> NS[ComponentData[D, CommandData], OutputEntry]:
    return (
        NS.inspect_maybe(__.lift(index), lambda: f'invalid output entry index {index}')
        .zoom(lens.comp.output.locations)
    )


def output_line_for(entry: OutputEntry) -> NS[ComponentData[D, CommandData], OutputLine]:
    return (
        NS.inspect_maybe(__.index_where(__.entry.contains(entry)), lambda: f'no matching line for location {entry}')
        .zoom(lens.comp.output.lines)
    )


@do(NvimIO[None])
def jump_to_location(scratch: ScratchBuffer, location: Location) -> Do:
    window = scratch.ui.previous
    yield focus_window(window)
    current_file = yield window_buffer_name(window)
    location_exists = yield NvimIO.from_io(IO.delay(location.file_path.exists))
    if location_exists:
        yield edit_file(location.file_path) if current_file != location.file_path else NvimIO.pure(None)
        yield set_local_cursor(location.coords)
    yield NvimIO.pure(None)


# FIXME entries can be identical, need uuid for lookup; or implement better model
@do(NS[ComponentData[D, CommandData], None])
def select_entry(index: int, auto_jump: Boolean) -> Do:
    yield NS.modify(__.set.current(index)).zoom(lens.comp.output)
    location = yield output_entry_at(index)
    line = yield output_line_for(location)
    scratch = yield scratch_buffer()
    yield NS.lift(set_line(scratch.ui.window, line + 1))
    yield NS.modify(__.set.current(index)).zoom(lens.comp.output)
    if auto_jump:
        yield NS.lift(jump_to_location(scratch, location))


@do(NS[ComponentData[MyoPluginState, CommandData], None])
def display_parse_result(result: ParseResult) -> Do:
    lines = result.lines
    locations = result.locations
    output_lens = lens.comp.output
    scratch = yield NS.lift(show_in_scratch_buffer(lines / _.formatted, CreateScratchBufferOptions.cons()))
    yield NS.modify(__.copy(lines=lines, locations=locations, scratch=Just(scratch))).zoom(output_lens)
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.main)
    auto_jump = yield setting(_.auto_jump).read_zoom(lens.main.resources)
    yield select_entry(0, auto_jump)


@trans.free.result(trans.st)
@do(NS[ComponentData[Env, CommandData], None])
def current_entry_jump() -> Do:
    output = yield output_data()
    scratch = yield scratch_buffer()
    line = yield NS.lift(window_line(scratch.ui.window))
    location = yield NS.from_maybe(output.lines.lift(line) / _.target, 'current line has no location')
    yield NS.lift(jump_to_location(scratch, location))


@trans.free.result(trans.st)
@do(NS[ComponentData[D, CommandData], None])
def quit_output() -> Do:
    scratch = yield scratch_buffer()
    yield NS.lift(close_buffer(scratch.buffer))
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], None])
def prev_entry() -> Do:
    current = yield NS.inspect(_.data.comp.output.current)
    auto_jump = yield setting(_.auto_jump)
    if current > 0:
        yield select_entry(current - 1, auto_jump).zoom(lens.data)


@trans.free.result(trans.st)
@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], None])
def next_entry() -> Do:
    current = yield NS.inspect(_.data.comp.output.current)
    count = yield NS.inspect(_.data.comp.output.locations.length)
    if current < count - 1:
        auto_jump = yield setting(_.auto_jump)
        yield select_entry(current + 1, auto_jump).zoom(lens.data)


__all__ = ('display_parse_result', 'current_entry_jump', 'quit_output', 'prev_entry', 'next_entry')
