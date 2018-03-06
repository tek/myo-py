from amino import do, _, Do, List
from amino.boolean import true
from amino.lenses.lens import lens

from ribosome.nvim.io import NS
from ribosome.nvim.scratch import show_in_scratch_buffer, CreateScratchBufferOptions
from ribosome.dispatch.component import ComponentData
from ribosome.trans.api import trans
from ribosome.trans.mapping import activate_mapping
from ribosome.dispatch.mapping import Mapping

from myo.components.command.data import CommandData
from myo.output.data import ParseResult
from myo.config.plugin_state import MyoPluginState

jump_mapping = Mapping.cons('<cr>', true)
quit_mappiing = Mapping.cons('q', true)
prev_mapping = Mapping.cons('<m-->', true)
next_mapping = Mapping.cons('<m-=>', true)


@do(NS[ComponentData[MyoPluginState, CommandData], None])
def display_parse_result(result: ParseResult) -> Do:
    yield NS.lift(show_in_scratch_buffer(result.lines / _.formatted, CreateScratchBufferOptions.cons()))
    yield List(jump_mapping).traverse(activate_mapping, NS).zoom(lens.main)
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[None, None])
def current_entry_jump() -> Do:
    yield NS.unit


__all__ = ('display_parse_result', 'current_entry_jump')
