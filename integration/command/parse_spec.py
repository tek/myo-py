from kallikrein import Expectation, k
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import equal
from kallikrein.matchers.tuple import tupled
from kallikrein.matchers.maybe import be_just

from chiasma.util.id import StrIdent

from amino import List, Map, Nothing, Path, do, Do, Nil, Just
from amino.test.spec import SpecBase

from ribosome.nvim.api.ui import (current_buffer_content, current_buffer_name, current_cursor, current_window,
                                  close_window, set_local_line)
from ribosome.compute.run import run_prog
from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.test.integration.external import external_state_test
from ribosome.test.klk.matchers.buffer import buffer_count_is
from ribosome.compute.ribosome_api import Ribo

from myo.data.command import Command, HistoryEntry
from myo.components.command.compute.parse import parse, ParseOptions
from myo.components.command.compute.output import (render_parse_result, current_event_jump, next_event, prev_event,
                                                   select_cursor_event)
from myo.output.data.output import OutputEvent
from myo.output.parser.python import PythonLine, PythonEvent
from myo.config.settings import auto_jump
from myo.components.command.compute.tpe import CommandRibosome
from myo.config.plugin_state import MyoState
from myo.components.command.compute.parsed_output import ParsedOutput
from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.lang.python.report import python_report
from myo.output.lang.python.syntax import python_syntax

from test.command import update_command_data, command_spec_test_config
from test.output.python import output_events, file_path, trace_file, line, col, parsed_output
from test.output.util import myo_syntax, myo_highlight

from integration._support.python_parse import events


@do(NS[MyoState, Expectation])
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


@do(NS[MyoState, Expectation])
def jump_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    yield run_prog(current_event_jump, Nil)
    name = yield NS.lift(current_buffer_name())
    cursor = yield NS.lift(current_cursor())
    return (k(name) == str(file_path)) & (k(cursor) == (line, col))


@do(NS[MyoState, Expectation])
def jump_last_line_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield NS.lift(set_local_line(1))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    yield run_prog(current_event_jump, Nil)
    name = yield NS.lift(current_buffer_name())
    cursor = yield NS.lift(current_cursor())
    return (k(name) == str(file_path)) & (k(cursor) == (line, col))


@do(NS[MyoState, Expectation])
def cycle_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    cursor1 = yield NS.lift(current_cursor())
    yield run_prog(next_event, Nil)
    cursor2 = yield NS.lift(current_cursor())
    yield run_prog(prev_event, Nil)
    cursor3 = yield NS.lift(current_cursor())
    return k((cursor1, cursor2, cursor3)).must(tupled(3)((equal((0, 0)), equal((2, 0)), equal((0, 0)))))


@do(NS[MyoState, Expectation])
def select_cycle_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    cursor1 = yield NS.lift(current_cursor())
    yield NS.lift(set_local_line(5))
    yield run_prog(prog.result(select_cursor_event), Nil)
    yield run_prog(next_event, Nil)
    cursor2 = yield NS.lift(current_cursor())
    return k((cursor1, cursor2)).must(tupled(2)((equal((0, 0)), equal((7, 0)))))


def first_error(output: List[OutputEvent[PythonLine, PythonEvent]]) -> NS[CommandRibosome, int]:
    return NS.pure(1)


@do(NS[MyoState, Expectation])
def first_error_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    parse_handlers = ParseHandlers.cons(first_error=Just(first_error))
    yield run_prog(prog.result(render_parse_result), List(ParsedOutput(parse_handlers, Nil, output_events)))
    cursor = yield NS.lift(current_cursor())
    return k(cursor) == (2, 0)


def truncate_path(path: Path) -> NS[CommandRibosome, str]:
    return NS.pure(path.name)


@do(NS[MyoState, Expectation])
def path_formatter_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    parse_handlers = ParseHandlers.cons(path_formatter=Just(truncate_path), reporter=Just(python_report))
    yield run_prog(prog.result(render_parse_result), List(ParsedOutput(parse_handlers, Nil, output_events)))
    content = yield NS.lift(current_buffer_content())
    return k(content.head).must(be_just('file.py  3 funcname'))


target_syntax = '''MyoPath        xxx match /^.*\ze\( .*$\)\@=/  contained containedin=MyoLocation
MyoLineNumber  xxx match /\( \)\@<=\zs\d\+\ze/  contained containedin=MyoLocation
MyoFunction    xxx match /\( \d\+ \)\@<=\zs.*$/  contained containedin=MyoLocation
MyoCode        xxx match /^    .*$/  contained contains=@python
MyoLocation    xxx match /^.*.*$/  contains=MyoPath,MyoLineNumber,MyoFunction nextgroup=MyoCode skipwhite skipnl
MyoException   xxx match /^\w\+:/  contained containedin=MyoError
MyoError       xxx match /^\w\+: .*$/  contains=MyoException
'''

target_highlight = '''MyoPath        xxx links to Directory
MyoLineNumber  xxx links to Directory
MyoFunction    xxx links to Type
MyoCode        xxx cleared
MyoLocation    xxx cleared
MyoException   xxx links to Error
MyoError       xxx cleared
'''


@do(NS[MyoState, Expectation])
def syntax_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    parse_handlers = ParseHandlers.cons(syntax=Just(python_syntax), reporter=Just(python_report))
    yield run_prog(prog.result(render_parse_result), List(ParsedOutput(parse_handlers, Nil, output_events)))
    syn = yield NS.lift(myo_syntax())
    hi = yield NS.lift(myo_highlight())
    return k(syn).must(have_lines(target_syntax)) & k(hi).must(have_lines(target_highlight))


@do(NS[MyoState, Expectation])
def twice_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    yield NS.lift(buffer_count_is(2))


@do(NS[MyoState, Expectation])
def reopen_spec() -> Do:
    yield NS.lift(auto_jump.update(False))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    window = yield NS.lift(current_window())
    yield NS.lift(close_window(window))
    yield run_prog(prog.result(render_parse_result), List(parsed_output))
    yield NS.lift(buffer_count_is(2))


class ParseSpec(SpecBase):
    '''
    parse command output $command_output
    jump to current error $jump
    jump to current error with cursor on last line of the event $jump_last_line
    cycle to next and previous error $cycle
    cycle after selecting error $select_cycle
    custom first error $first_error
    custom path formatter $path_formatter
    apply syntax rules $syntax
    render twice $twice
    reopen $reopen
    '''

    def command_output(self) -> Expectation:
        return external_state_test(command_spec_test_config, command_output_spec)

    def jump(self) -> Expectation:
        return external_state_test(command_spec_test_config, jump_spec)

    def jump_last_line(self) -> Expectation:
        return external_state_test(command_spec_test_config, jump_last_line_spec)

    def cycle(self) -> Expectation:
        return external_state_test(command_spec_test_config, cycle_spec)

    def select_cycle(self) -> Expectation:
        return external_state_test(command_spec_test_config, select_cycle_spec)

    def first_error(self) -> Expectation:
        return external_state_test(command_spec_test_config, first_error_spec)

    def path_formatter(self) -> Expectation:
        return external_state_test(command_spec_test_config, path_formatter_spec)

    def syntax(self) -> Expectation:
        return external_state_test(command_spec_test_config, syntax_spec)

    def twice(self) -> Expectation:
        return external_state_test(command_spec_test_config, twice_spec)

    def reopen(self) -> Expectation:
        return external_state_test(command_spec_test_config, reopen_spec)


__all__ = ('ParseSpec',)
