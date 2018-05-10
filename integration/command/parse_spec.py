from kallikrein import Expectation, k, pending
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import equal
from kallikrein.matchers.tuple import tupled

from chiasma.util.id import StrIdent

from amino import List, Map, Nothing, Path, do, Do, Nil, Just
from amino.test import fixture_path
from amino.test.spec import SpecBase

from ribosome.nvim.api.ui import current_buffer_content, current_buffer_name, current_cursor, current_window
from ribosome.compute.run import run_prog
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.io.api import N

from myo.data.command import Command, HistoryEntry
from myo.components.command.compute.parse import parse, ParseOptions
from myo.components.command.compute.output import render_parse_result, current_entry_jump, next_entry, prev_entry
from myo.output.data import ParseResult, CodeEntry, OutputEvent
from myo.output.parser.python import FileEntry, PyErrorEntry, ColEntry
from myo.settings import auto_jump

from test.command import update_command_data, command_spec_test_config

from integration._support.python_parse import events


line, col = 2, 5
line1 = 3
file_path = fixture_path('command', 'parse', 'file.py')
entry = FileEntry(
    f'  File "{file_path}", line {line}, in funcname',
    Path(file_path),
    line,
    col,
    Just('funcname'),
    Just(CodeEntry('    yield', 'yield'))
)
entry1 = entry.set.col(line1)
output_events = List(
    OutputEvent(
        Nil,
        List(
            entry,
            entry1,
            PyErrorEntry('RuntimeError: error', 'error', 'RuntimeError')
        )
    ),
    OutputEvent(
        Nil,
        List(
            entry,
            entry1,
            ColEntry('           ^', ' '),
            PyErrorEntry('SyntaxError: error', 'error', 'SyntaxError')
        )
    )
)
parse_result = ParseResult(Nil, output_events, List('python'))
trace_file = fixture_path('tmux', 'python_parse', 'trace')


@do(NS[PS, Expectation])
def command_output_spec() -> Do:
    cmd_ident = StrIdent('commo')
    cmd = Command.cons(cmd_ident)
    hist = HistoryEntry(cmd, Nothing)
    logs = Map({cmd_ident: trace_file})
    yield update_command_data(commands=List(cmd), history=List(hist), logs=logs)
    yield NS.lift(auto_jump.update(False))
    yield run_prog(parse, List(ParseOptions.cons()))
    content = yield NS.lift(current_buffer_content())
    return k(content).must(have_lines(events))


@do(NS[PS, Expectation])
def jump_spec() -> Do:
    yield run_prog(prog.result(render_parse_result), List(parse_result))
    yield run_prog(current_entry_jump, Nil)
    name = yield NS.lift(current_buffer_name())
    cursor = yield NS.lift(current_cursor())
    return (k(name) == str(file_path)) & (k(cursor) == (line, col))


@do(NS[PS, Expectation])
def next_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parse_result))
    cursor1 = yield NS.lift(current_cursor())
    yield run_prog(next_entry, Nil)
    cursor2 = yield NS.lift(current_cursor())
    yield run_prog(prev_entry, Nil)
    cursor3 = yield NS.lift(current_cursor())
    return k((cursor1, cursor2, cursor3)).must(tupled(3)((equal((1, 0)), equal((3, 0)), equal((1, 0)))))


class ParseSpec(SpecBase):
    '''
    parse command output $command_output
    jump to current error $jump
    cycle to next error $next
    '''

    def command_output(self) -> Expectation:
        return external_state_test(command_spec_test_config, command_output_spec)

    @pending
    def jump(self) -> Expectation:
        return external_state_test(command_spec_test_config, jump_spec)

    def next(self) -> Expectation:
        return external_state_test(command_spec_test_config, next_spec)


__all__ = ('ParseSpec',)
