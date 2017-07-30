from typing import Any

from kallikrein.matchers import contain
from kallikrein.matchers.length import have_length
from kallikrein import unsafe_k, kf, Expectation, k
from kallikrein.matchers.comparison import not_equal

from amino.test.path import fixture_path
from amino import Map, Just, List, _, __, Path, Maybe
from amino.lazy import lazy
from amino.test import temp_file

from ribosome.machine.scratch import Mapping
from ribosome.test.integration.klk import later, later_f

from myo.command import ShellCommand
from myo.plugins.core.message import ParseOutput
from myo.output.machine import (error_filtered_result_empty, EventNext, EventPrev, OutputMachine, OMState)
from myo.plugins.core.main import error_no_output_events
from myo.output.data import ParseResult

from integration._support.base import MyoIntegrationSpec

_trace_len = 3
_line_count = _trace_len * 4 + 2
_initial_error_num = 2


class ParseHelpers(MyoIntegrationSpec):

    def _modifiable(self, val: bool) -> Expectation:
        return later(kf(lambda: self.vim.buffer.options('modifiable')).must(contain(val)))

    @lazy
    def _file(self) -> Path:
        path = temp_file('core', 'parse', 'python', 'code.py')
        path.write_text(self._python_code.join_lines)
        return path

    @property
    def _python_func_name(self) -> str:
        return 'func_name'

    @lazy
    def _python_code(self) -> List[str]:
        fun = List(
            '',
            'def {}(a, b=1):'.format(self._python_func_name),
            '    return 1',
        )
        return (fun * 10).cons('import functools')

    def _frame(self, i: int) -> List[str]:
        return List(
            '  File "{}", line {}, in {}'.format(self._file, i + 1, self._python_func_name),
            '    {}()'.format(List.random_string(4))
        )

    def _mk_trace_with(self, length: int) -> List[str]:
        t = List.range(length) // self._frame
        err = 'AttributeError: butt'
        return t.cat(err)

    @property
    def _mk_trace(self) -> List[str]:
        return self._mk_trace_with(_trace_len)

    @property
    def _output_machine(self) -> OutputMachine:
        return (
            self.root.sub
            .find_type(OutputMachine)
            .get_or_fail('no output machine!')
        )

    @property
    def _state(self) -> OMState:
        return (
            self.root.data
            .sub_state_m('output')
            .get_or_fail('no output state')
        )


class NativeParseSpec(ParseHelpers):
    '''parse error output using 'errorformat' $native
    '''

    def _set_vars(self) -> None:
        super()._set_vars()
        errorformat = List(
            '%AIn %f:%l',
            '%C  %.%#',
            '%+Z%.%#Error: %.%#'
        ).mk_string(',')
        self.vim.buffer.options.set('errorformat', errorformat)

    def native(self) -> Expectation:
        cmd = ShellCommand(name='a', line='a', parser=Just('s:compiler'))
        fix = fixture_path('parse', 'err1')
        output = List.wrap(fix.read_text().splitlines())
        msg = ParseOutput(cmd, output, fix, Map())
        self.root.send(msg)
        self._await()
        qf = self.vim.call('getqflist') | []
        return k(len(qf)).must(not_equal(0))


class ParseTwiceSpec(ParseHelpers):
    '''parse the same output twice, quitting in between $twice
    '''

    def twice(self) -> Expectation:
        self.vim.vars.set_p('jump_to_error', False)
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, self._mk_trace, None, Map())
        self.root.send_sync(msg)
        self._modifiable(False)
        self.root.send_sync(Mapping(self._output_machine.uuid, 'q'))
        self._modifiable(True)
        self.root.send_sync(msg)
        return self._modifiable(False)


class ParseEmptySpec(ParseHelpers):
    '''parsing empty output prints an error $empty
    '''

    def empty(self) -> None:
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, List(), None, Map())
        self.root.send_sync(msg)
        return self._messages_contain(error_no_output_events)
        return self._window_count(1)


class ParseOpenModifiedSpec(ParseHelpers):
    '''jumping to an error with a modified open buffer
    buffer is saved and changed $modified
    '''

    def modified(self) -> None:
        self.vim.edit(self._file).run_sync()
        self.vim.buffer.options.set('modified', True)
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, self._mk_trace, None, Map())
        l = self.vim.window.line
        self.root.send_sync(msg)
        later(kf(lambda: self.vim.window.line).must(not_equal(l)))
        return self._buffer_option('modified', True)


class ParseSpecBase(ParseHelpers):

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('jump_to_error', False)

    def _cursor(self, x: int, y: int) -> Expectation:
        return later(kf(lambda: self.vim.window.cursor) == List(x, y))


class PythonParseSpec(ParseSpecBase):
    '''
    parse python stack traces
    press <cr> to jump to an output entry location $jump
    specify a filter callback $filter
    specify callback that determines initially selected output entry $initial_pos
    default initial entry $initial_pos_default
    first initial entry $initial_pos_first
    immediately jump to location of initial entry determined by callback $initial_pos_with_jump
    jump to location of default initial entry $default_jump
    format output events with a language specific reifier $lang_reifier
    parse different traces after another $twice
    # syntax test $syntax
    filter duplicate traces $duplicate
    empty result after filter $empty_filtered
    cycle through output events $cycle
    '''

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.vars.set_p('output_reifier', 'py:myo.output.reifier.base.LiteralReifier')

    def _parse(self, output: List[str], parse_opt: Map=Map()) -> List[str]:
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, output, None, parse_opt)
        self.root.send_sync(msg)
        return output

    def _run(self, output: List[str], parse_opt: Map=Map()) -> List[str]:
        return self._parse(output, parse_opt)

    def _init(self, parse_opt: Map=Map()) -> List[str]:
        trace1 = self._mk_trace
        trace2 = self._mk_trace
        output = trace1 + trace2
        return self._run(output, parse_opt)

    def _go(self, line_count: int=_line_count, parse_opt: Map=Map()) -> Expectation:
        output = self._init(parse_opt)
        self._buffer_contains(output[-1])
        self._buffer_option('modifiable', False)
        return self._buffer_length(line_count)

    def _check_jumped(self, line: int) -> None:
        unsafe_k(self.vim.window.buffer.name) == str(self._file)
        return self._cursor(line, 0)

    def jump(self) -> Expectation:
        self._go()
        self.vim.window.set_cursor(_trace_len * 2)
        self.root.send_sync(Mapping(self._output_machine.uuid, '%cr%'))
        self._window_count(2)
        return self._check_jumped(_trace_len)

    def filter(self) -> Expectation:
        def toggle() -> None:
            self.root.send_sync(Mapping(self._output_machine.uuid, 'f'))
        filters = List('py:integration.core.parse_spec._filter1')
        count = _trace_len * 2 + 1
        self._go(count, Map(output_filters=filters))
        toggle()
        self._buffer_length(_line_count)
        toggle()
        return self._buffer_length(count)

    def initial_pos(self) -> Expectation:
        self.vim.vars.set_p('initial_error', ['py:integration.core.parse_spec._initial_error'])
        self._go()
        unsafe_k(self._state.current_loc_index) == _initial_error_num
        return self._cursor_line(_initial_error_num * 2 + 1)

    def initial_pos_default(self) -> Expectation:
        self._go()
        return self._cursor_line(_line_count - 2)

    def initial_pos_first(self) -> Expectation:
        self.vim.vars.set_p('initial_error', ['s:first'])
        self._go()
        return self._cursor_line(1)

    def initial_pos_with_jump(self) -> Expectation:
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.vars.set_p('initial_error', ['py:integration.core.parse_spec._initial_error'])
        self._init()
        return self._check_jumped(_initial_error_num % _trace_len + 1)

    def default_jump(self) -> Expectation:
        self.vim.vars.set_p('jump_to_error', True)
        self._init()
        return self._check_jumped(3)

    def lang_reifier(self) -> Expectation:
        self.vim.vars.set_p('output_reifier', 'py:myo.output.reifier.python.Reifier')
        trace1 = self._mk_trace_with(1)
        self._run(trace1)
        return self._cursor(1, 0)

    def twice(self) -> Expectation:
        t1 = self._mk_trace_with(1)
        t2 = self._mk_trace_with(1)
        def check(t: List[str]) -> Expectation:
            return self._buffer_line(-2, t.lift(-2) | 'invalid')
        self._run(t1)
        check(t1)
        h = self.vim.window.height
        self.vim.windows.last % __.focus()
        self._parse(t2)
        check(t2)
        return self._window_height(h | -1)

    def syntax(self) -> Expectation:
        from amino import log
        self.vim.vars.set_p('output_reifier', '')
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        self._init()
        self._wait(3)
        log.info(self.vim.cmd_output('syntax').join_lines)
        self._check_jumped(2)

    def duplicate(self) -> Expectation:
        t = self._mk_trace_with(2)
        trace = t + t
        self._run(trace)
        return self._buffer_content(t)

    def empty_filtered(self) -> Expectation:
        filters = List('py:integration.core.parse_spec._filter_empty')
        self.vim.vars.set_p('output_reifier', 'py:myo.output.reifier.python.Reifier')
        self._init(Map(output_filters=filters))
        return self._messages_contain(error_filtered_result_empty)

    def cycle(self) -> Expectation:
        self.vim.vars.set_p('initial_error', ['s:first'])
        self._go()
        self.root.send_sync(EventNext())
        self._cursor_line(2)
        self.root.send_sync(EventNext())
        self._cursor_line(3)
        self.root.send_sync(EventPrev())
        return self._cursor_line(2)


def _filter1(result: ParseResult) -> ParseResult:
    e = result.events
    e2 = e[:1] + e[1 + _trace_len * 2 + 2:]
    return result.set(events=e2)


def _filter_empty(result: ParseResult) -> ParseResult:
    return result.set(events=List())


def _initial_error(a: Any) -> Maybe[int]:
    return Just(_initial_error_num)


class SbtParseSpec(ParseSpecBase):
    '''parse scala compiler output
    complete process $complete
    specify filter, formatter and truncator python callback via variables $filter_format
    # syntax test $syntax
    '''

    @lazy
    def _scala_file(self) -> Path:
        path = temp_file('core', 'parse', 'sbt', 'code.scala')
        path.write_text(self._scala_code.join_lines)
        return path

    @property
    def _line(self) -> int:
        return 3

    @property
    def _scala_func_name(self) -> str:
        return 'scalafunc'

    @lazy
    def _scala_code(self) -> List[str]:
        return List(
            'import foo.bar',
            'class Foo {',
            'def {}(a: Int): Int = a'.format(self._scala_func_name),
            '}',
        )

    @property
    def _mk_scala_error(self) -> List[str]:
        l = 4
        tmpl = '[error] {}:{}: butt'
        return List(
            tmpl.format(self._scala_file, self._line),
            '[error] {}()'.format(List.random_string(l)),
            '[error] {}^'.format(' ' * l),
        )

    def _mk_scala_errors(self, count: int) -> List[List[str]]:
        return List.gen(count, lambda: self._mk_scala_error)

    def _run(self, output: List[str]) -> None:
        cmd = ShellCommand(name='a', line='a', langs=List('sbt'))
        msg = ParseOutput(cmd, output, None, Map())
        self.root.send_sync(msg)

    def complete(self) -> Expectation:
        self.vim.vars.set_p('output_reifier', 'py:myo.output.reifier.base.LiteralReifier')
        output = self._mk_scala_errors(1)
        self._run(output)
        unsafe_k(self.vim.buffer.content).must(contain(output[-1]))
        unsafe_k(self.vim.buffer.options('modifiable')).must(contain(False))
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(self._output_machine.uuid, '%cr%'))
        unsafe_k(self.vim.windows).must(have_length(2))
        unsafe_k(self.vim.window.buffer.name) == str(self._scala_file)
        return self._cursor(3, 4)

    def filter_format(self) -> Expectation:
        def check() -> Expectation:
            return (
                self._buffer_length(8) &
                self._buffer_line(0, '{}  3'.format(self._scala_file.name)) &
                self._window_height(8)
            )
        filters = List('py:integration.core.parse_spec._filter')
        formatters = List('py:integration.core.parse_spec._format')
        trunc = 'py:integration.core.parse_spec._trunc'
        self.vim.vars.set_p('output_filters', filters)
        self.vim.vars.set_p('output_formatters', formatters)
        self.vim.vars.set_p('path_truncator', trunc)
        output = self._mk_scala_errors(4)
        self._run(output)
        return later_f(check)

    def syntax(self) -> Expectation:
        from amino import log
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        output = self._mk_scala_errors(1)
        self._run(output)
        self._wait(2)
        log.info(self.vim.cmd_output('syntax').join_lines)
        return k(1) == 1


def _filter(r: ParseResult) -> ParseResult:
    return r.modder.events(_[2:])


def _format(r: ParseResult) -> ParseResult:
    return r


def _trunc(path: Path) -> str:
    return path.name

__all__ = ('NativeParseSpec', 'ParseTwiceSpec', 'ParseEmptySpec', 'ParseOpenModifiedSpec', 'PythonParseSpec',
           'SbtParseSpec')
