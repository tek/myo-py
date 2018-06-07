from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import equal
from kallikrein.matchers.tuple import tupled

from chiasma.util.id import StrIdent

from amino import List, Map, Nothing, Path, do, Do, Nil, Just
from amino.test import fixture_path
from amino.test.spec import SpecBase
from amino.lenses.lens import lens

from ribosome.nvim.api.ui import current_buffer_content, current_buffer_name, current_cursor
from ribosome.compute.run import run_prog
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.integration.external import external_state_test

from myo.data.command import Command, HistoryEntry
from myo.components.command.compute.parse import parse, ParseOptions
from myo.components.command.compute.output import render_parse_result, current_event_jump, next_event, prev_event
from myo.output.data.output import OutputEvent, OutputLine
from myo.output.parser.python import FileLine, ErrorLine, ColLine, CodeLine, python_event
from myo.settings import auto_jump

from test.command import update_command_data, command_spec_test_config

from integration._support.python_parse import events


line, col = 2, 5
line1 = 3
line2 = 6
line3 = 7
file_path = fixture_path('command', 'parse', 'file.py')
output_line = OutputLine(
    f'  File "{file_path}", line {line}, in funcname',
    FileLine(
        Path(file_path),
        line,
        Just('funcname'),
    )
)
col5 = Just(OutputLine('    ^', ColLine(5)))
line_lens = lens.meta.line
code = OutputLine('    yield', CodeLine('yield'))
output_events = List(
    python_event(output_line, Just(code), col5),
    python_event(line_lens.set(line1)(output_line), Just(code), col5),
    OutputEvent.cons(List(OutputLine('RuntimeError: error', ErrorLine('error', 'RuntimeError')))),
    python_event(line_lens.set(line2)(output_line), Just(code), col5),
    python_event(line_lens.set(line3)(output_line), Just(code), col5),
    OutputEvent.cons(List(OutputLine('SyntaxError: error', ErrorLine('error', 'SyntaxError')))),
)
trace_file = fixture_path('tmux', 'python_parse', 'trace')


@do(NS[PS, Expectation])
def command_output_spec() -> Do:
    cmd_ident = StrIdent('commo')
    cmd = Command.cons(cmd_ident, langs=List('python'))
    hist = HistoryEntry(cmd, Nothing)
    logs = Map({cmd_ident: trace_file})
    yield update_command_data(commands=List(cmd), history=List(hist), logs=logs)
    yield NS.lift(auto_jump.update(False))
    yield run_prog(parse, List(ParseOptions.cons()))
    content = yield NS.lift(current_buffer_content())
    return k(content).must(have_lines(events))


@do(NS[PS, Expectation])
def jump_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(output_events))
    yield run_prog(current_event_jump, Nil)
    name = yield NS.lift(current_buffer_name())
    cursor = yield NS.lift(current_cursor())
    return (k(name) == str(file_path)) & (k(cursor) == (line, col))


@do(NS[PS, Expectation])
def next_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(output_events))
    cursor1 = yield NS.lift(current_cursor())
    yield run_prog(next_event, Nil)
    cursor2 = yield NS.lift(current_cursor())
    a = yield NS.lift(current_buffer_content())
    yield run_prog(prev_event, Nil)
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

    def jump(self) -> Expectation:
        return external_state_test(command_spec_test_config, jump_spec)

    def next(self) -> Expectation:
        return external_state_test(command_spec_test_config, next_spec)


__all__ = ('ParseSpec',)
