from typing import TypeVar

from amino import do, _, Do, List, __, Just
from amino.boolean import true
from amino.lenses.lens import lens

from ribosome.nvim.io import NS
from ribosome.nvim.scratch import show_in_scratch_buffer, CreateScratchBufferOptions, ScratchBuffer
from ribosome.dispatch.component import ComponentData
from ribosome.trans.api import trans
from ribosome.trans.mapping import activate_mapping
from ribosome.dispatch.mapping import Mapping
from ribosome.nvim.api import close_current_buffer, window_line, focus_window, edit_file, set_current_cursor
from ribosome import ribo_log
from ribosome.nvim import NvimIO

from myo.components.command.data import CommandData, OutputData
from myo.output.data import ParseResult
from myo.config.plugin_state import MyoPluginState
from myo.env import Env

D = TypeVar('D')
jump_mapping = Mapping.cons('<cr>', true)
quit_mapping = Mapping.cons('q', true)
prev_mapping = Mapping.cons('<m-->', true)
next_mapping = Mapping.cons('<m-=>', true)


def output_data() -> NS[ComponentData[D, CommandData], OutputData]:
    return NS.inspect(_.comp.output)


def scratch_buffer() -> NS[ComponentData[D, CommandData], ScratchBuffer]:
    return NS.inspect_either(__.to_either('no scratch buffer set')).zoom(lens.comp.output.scratch)


@do(NS[ComponentData[MyoPluginState, CommandData], None])
def display_parse_result(result: ParseResult) -> Do:
    lines = result.lines
    locations = result.locations
    output_lens = lens.comp.output
    scratch = yield NS.lift(show_in_scratch_buffer(lines / _.formatted, CreateScratchBufferOptions.cons()))
    yield NS.modify(__.copy(lines=lines, locations=locations, scratch=Just(scratch))).zoom(output_lens)
    yield List(jump_mapping, quit_mapping, prev_mapping, next_mapping).traverse(activate_mapping, NS).zoom(lens.main)
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[ComponentData[Env, CommandData], None])
def current_entry_jump() -> Do:
    output = yield output_data()
    scratch = yield scratch_buffer()
    line = yield NS.lift(window_line(scratch.ui.window))
    location = yield NS.from_maybe(output.lines.lift(line) / _.target, 'current line has no location')
    yield NS.lift(scratch.ui.previous / focus_window | NvimIO.pure(None))
    yield NS.lift(edit_file(location.file_path))
    yield NS.lift(set_current_cursor(location.coords))
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[None, None])
def quit_output() -> Do:
    yield NS.lift(close_current_buffer())
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[None, None])
def prev_entry() -> Do:
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[None, None])
def next_entry() -> Do:
    yield NS.unit


__all__ = ('display_parse_result', 'current_entry_jump', 'quit_output', 'prev_entry', 'next_entry')
