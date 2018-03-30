from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers import contain

from chiasma.util.id import StrIdent

from amino import List, Map, Nothing, Path, do, Do, Nil, Just
from amino.test import fixture_path

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk import kn
from ribosome.dispatch.component import ComponentData
from ribosome.nvim.api.ui import current_buffer_content, current_buffer_name, current_cursor

from myo.data.command import Command, HistoryEntry
from myo.components.command.trans.parse import parse
from myo.components.command.trans.output import display_parse_result, current_entry_jump, next_entry, prev_entry
from myo.output.data import ParseResult, CodeEntry, OutputEvent
from myo.output.parser.python import FileEntry, PyErrorEntry, ColEntry

from integration._support.spec import ExternalSpec
from integration._support.python_parse import events
from integration._support.command.setup import command_spec_data


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


class ParseSpec(ExternalSpec):
    '''
    parse command output $command_output
    jump to current error $jump
    cycle to next error $next
    '''

    def command_output(self) -> Expectation:
        cmd_ident = StrIdent('commo')
        cmd = Command.cons(cmd_ident)
        hist = HistoryEntry(cmd, Nothing)
        logs = Map({cmd_ident: trace_file})
        @do(NvimIO[List[str]])
        def run() -> Do:
            helper, aff, data = yield command_spec_data(commands=List(cmd), history=List(hist), logs=logs)
            yield helper.settings.auto_jump.update(False)
            yield parse.fun().run(helper.state.resources_with(ComponentData(helper.state, data)))
            yield current_buffer_content()
        return kn(self.vim, run).must(contain(have_lines(events)))

    def jump(self) -> Expectation:
        @do(NvimIO[List[str]])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            (s1, ignore) = yield display_parse_result(parse_result).run(ComponentData(helper.state, data))
            (s2, ignore) = yield current_entry_jump.fun().run(s1)
            name = yield current_buffer_name()
            cursor = yield current_cursor()
            return name, cursor
        return kn(self.vim, run).must(contain((str(file_path), (line, col))))

    def next(self) -> Expectation:
        @do(NvimIO[List[str]])
        def run() -> Do:
            helper, aff, data = yield command_spec_data()
            yield helper.settings.auto_jump.update(False)
            data = ComponentData(helper.state, data)
            (s1, ignore) = yield display_parse_result(parse_result).run(data)
            cursor1 = yield current_cursor()
            (s2, ignore) = yield next_entry.fun().run(helper.state.resources_with(s1))
            cursor2 = yield current_cursor()
            data = ComponentData(helper.state, data)
            yield prev_entry.fun().run(s2)
            cursor3 = yield current_cursor()
            return cursor1, cursor2, cursor3
        return kn(self.vim, run).must(contain(((1, 0), (3, 0), (1, 0))))


__all__ = ('ParseSpec',)
