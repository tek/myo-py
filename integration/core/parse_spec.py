from integration._support.base import MyoIntegrationSpec

from amino.test.path import fixture_path
from amino import Map, Just, List, _, __
from amino.test import temp_file, later
from amino.lazy import lazy

from ribosome.test.integration import main_looped
from ribosome.machine.scratch import Mapping

from myo.command import ShellCommand
from myo.plugins.core.message import ParseOutput
from myo.output.machine import (error_filtered_result_empty, EventNext,
                                EventPrev, OutputMachine)
from myo.plugins.core.main import error_no_output_events

_trace_len = 3
_line_count = _trace_len * 4 + 2
_initial_error_num = 2


class ParseHelpers:

    def _modifiable(self, val):
        later(lambda: self.vim.buffer.options('modifiable').should.contain(val)
              )

    @lazy
    def _file(self):
        path = temp_file('core', 'parse', 'python', 'code.py')
        path.write_text(self._python_code.join_lines)
        return path

    @property
    def _python_func_name(self):
        return 'func_name'

    @lazy
    def _python_code(self):
        fun = List(
            '',
            'def {}(a, b=1):'.format(self._python_func_name),
            '    return 1',
        )
        return (fun * 10).cons('import functools')

    def _frame(self, i):
        r = lambda: List.random_string(4)
        tmpl = '  File "{}", line {}, in {}'
        return List(
            tmpl.format(self._file, i + 1, self._python_func_name),
            '    {}()'.format(r())
        )

    def _mk_trace_with(self, length):
        t = List.range(length) // self._frame
        err = 'AttributeError: butt'
        return t.cat(err)

    @property
    def _mk_trace(self):
        return self._mk_trace_with(_trace_len)

    @property
    def _output_machine(self):
        return (
            self.root.sub
            .find_type(OutputMachine)
            .get_or_fail('no output machine!')
        )

    @property
    def _state(self):
        return (
            self.root.data
            .sub_state_m('output')
            .get_or_fail('no output state')
        )


class NativeParseSpec(MyoIntegrationSpec, ParseHelpers):

    def _set_vars(self):
        super()._set_vars()
        errorformat = List(
            '%AIn %f:%l',
            '%C  %.%#',
            '%+Z%.%#Error: %.%#'
        ).mk_string(',')
        self.vim.buffer.options.set('errorformat', errorformat)

    @main_looped
    def native(self):
        cmd = ShellCommand(name='a', line='a', parser=Just('s:compiler'))
        fix = fixture_path('parse', 'err1')
        output = List.wrap(fix.read_text().splitlines())
        msg = ParseOutput(cmd, output, fix, Map())
        self.root.send(msg)
        self._await()
        qf = self.vim.call('getqflist') | []
        qf.should_not.be.empty


class ParseTwiceSpec(MyoIntegrationSpec, ParseHelpers):

    @main_looped
    def twice(self):
        self.vim.vars.set_p('jump_to_error', False)
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, self._mk_trace, None, Map())
        self.root.send_sync(msg)
        self._modifiable(False)
        self.root.send_sync(Mapping(self._output_machine.uuid, 'q'))
        self._modifiable(True)
        self.root.send_sync(msg)
        self._modifiable(False)


class ParseEmptySpec(MyoIntegrationSpec, ParseHelpers):

    def empty(self):
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, List(), None, Map())
        self.root.send_sync(msg)
        later(lambda:
              self.vim.messages.should.contain(error_no_output_events))
        self.vim.windows.should.have.length_of(1)


class ParseOpenModifiedSpec(MyoIntegrationSpec, ParseHelpers):

    def modified(self):
        self.vim.edit(self._file).run_sync()
        self.vim.buffer.options.set('modified', True)
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, self._mk_trace, None, Map())
        l = self.vim.window.line
        self.root.send_sync(msg)
        later(lambda: self.vim.window.line.should_not.equal(l))
        self.vim.buffer.options('modified').should.be.true


class ParseSpecBase(MyoIntegrationSpec, ParseHelpers):

    def _pre_start(self):
        super()._pre_start()
        self.vim.vars.set_p('jump_to_error', False)

    def _cursor(self, x, y):
        later(lambda: self.vim.window.cursor.should.equal(List(x, y)))


class PythonParseSpec(ParseSpecBase):

    def _pre_start(self):
        super()._pre_start()
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.base.LiteralReifier')

    def _parse(self, output, parse_opt=Map()):
        cmd = ShellCommand(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, output, None, parse_opt)
        self.root.send_sync(msg)
        return output

    def _run(self, output, parse_opt=Map()):
        return self._parse(output, parse_opt)

    def _init(self, parse_opt=Map()):
        trace1 = self._mk_trace
        trace2 = self._mk_trace
        output = trace1 + trace2
        return self._run(output, parse_opt)

    def _go(self, line_count=_line_count, parse_opt=Map()):
        output = self._init(parse_opt)
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.options('modifiable').should.contain(False)
        self.vim.buffer.content.should.have.length_of(line_count)

    def _check_jumped(self, line):
        self.vim.window.buffer.name.should.equal(str(self._file))
        self._cursor(line, 0)

    def jump(self):
        self._go()
        self.vim.window.set_cursor(_trace_len * 2)
        self.root.send_sync(Mapping(self._output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self._check_jumped(_trace_len)

    def filter(self):
        filters = List('py:integration.core.parse_spec._filter1')
        count = _trace_len * 2 + 1
        self._go(count, Map(output_filters=filters))
        toggle = lambda: self.root.send_sync(Mapping(self._output_machine.uuid,
                                                     'f'))
        toggle()
        later(lambda: self._buffer_length(_line_count))
        toggle()
        later(lambda: self._buffer_length(count))

    def initial_pos(self):
        self.vim.vars.set_p('initial_error',
                            ['py:integration.core.parse_spec._initial_error'])
        self._go()
        self._state.current_loc_index.should.equal(_initial_error_num)
        self.vim.window.line.should.contain(_initial_error_num * 2 + 1)

    def initial_pos_default(self):
        self._go()
        self.vim.window.line.should.contain(_line_count - 2)

    def initial_pos_first(self):
        self.vim.vars.set_p('initial_error', ['s:first'])
        self._go()
        self.vim.window.line.should.contain(1)

    def initial_pos_with_jump(self):
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.vars.set_p('initial_error',
                            ['py:integration.core.parse_spec._initial_error'])
        self._init()
        self._check_jumped(_initial_error_num % _trace_len + 1)

    def default_jump(self):
        self.vim.vars.set_p('jump_to_error', True)
        self._init()
        self._check_jumped(3)

    def lang_reifier(self):
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.python.Reifier')
        trace1 = self._mk_trace_with(1)
        self._run(trace1)
        self._cursor(1, 0)

    def twice(self):
        t1 = self._mk_trace_with(1)
        t2 = self._mk_trace_with(1)
        def check(t):
            later(lambda: self.vim.buffer.content.lift(-2)
                  .should.equal(t.lift(-2)))
        self._run(t1)
        check(t1)
        h = self.vim.window.height
        self.vim.windows.last % __.focus()
        self._parse(t2)
        check(t2)
        self.vim.window.height.should.equal(h)

    def _syntax(self):
        from amino import log
        self.vim.vars.set_p('output_reifier', '')
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        self._init()
        self._wait(3)
        log.info(self.vim.cmd_output('syntax').join_lines)
        self._check_jumped(2)

    def duplicate(self):
        t = self._mk_trace_with(2)
        trace = t + t
        self._run(trace)
        later(lambda: self.vim.buffer.content.should.equal(t))

    def _empty_filtered(self):
        filters = List('py:integration.core.parse_spec._filter_empty')
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.python.Reifier')
        self._init(Map(output_filters=filters))
        later(lambda:
              self.vim.messages.should.contain(error_filtered_result_empty))

    def cycle(self):
        pos = lambda l: later(lambda: self.vim.window.line.should.contain(l))
        self.vim.vars.set_p('initial_error', ['s:first'])
        self._go()
        self.root.send_sync(EventNext())
        pos(2)
        self.root.send_sync(EventNext())
        pos(3)
        self.root.send_sync(EventPrev())
        pos(2)


def _filter1(result):
    e = result.events
    e2 = e[:1] + e[1 + _trace_len * 2 + 2:]
    return result.set(events=e2)


def _filter_empty(result):
    return result.set(events=List())


def _initial_error(a):
    return Just(_initial_error_num)


class SbtParseSpec(ParseSpecBase):

    @lazy
    def _scala_file(self):
        path = temp_file('core', 'parse', 'sbt', 'code.scala')
        path.write_text(self._scala_code.join_lines)
        return path

    @property
    def _line(self):
        return 3

    @property
    def _scala_func_name(self):
        return 'scalafunc'

    @lazy
    def _scala_code(self):
        return List(
            'import foo.bar',
            'class Foo {',
            'def {}(a: Int): Int = a'.format(self._scala_func_name),
            '}',
        )

    @property
    def _mk_scala_error(self):
        l = 4
        r = lambda: List.random_string(l)
        tmpl = '[error] {}:{}: butt'
        return List(
            tmpl.format(self._scala_file, self._line),
            '[error] {}()'.format(r()),
            '[error] {}^'.format(' ' * l),
        )

    def _mk_scala_errors(self, count):
        return List.gen(count, lambda: self._mk_scala_error)

    def _run(self, output):
        cmd = ShellCommand(name='a', line='a', langs=List('sbt'))
        msg = ParseOutput(cmd, output, None, Map())
        self.root.send_sync(msg)

    def complete(self):
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.base.LiteralReifier')
        output = self._mk_scala_errors(1)
        self._run(output)
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.options('modifiable').should.contain(False)
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(self._output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self.vim.window.buffer.name.should.equal(str(self._scala_file))
        self._cursor(3, 4)

    def filter_format(self):
        def check():
            c = self.vim.buffer.content
            c.should.have.length_of(8)
            c.head.should.contain('{}  3'.format(self._scala_file.name))
            self.vim.window.height.should.contain(8)
        filters = List('py:integration.core.parse_spec._filter')
        formatters = List('py:integration.core.parse_spec._format')
        trunc = 'py:integration.core.parse_spec._trunc'
        self.vim.vars.set_p('output_filters', filters)
        self.vim.vars.set_p('output_formatters', formatters)
        self.vim.vars.set_p('path_truncator', trunc)
        output = self._mk_scala_errors(4)
        self._run(output)
        later(check)

    def _syntax(self):
        from amino import log
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        output = self._mk_scala_errors(1)
        self._run(output)
        self._wait(2)
        log.info(self.vim.cmd_output('syntax').join_lines)


def _filter(r):
    return r.modder.events(_[2:])


def _format(r):
    return r


def _trunc(path):
    return path.name

__all__ = ('PythonParseSpec', 'SbtParseSpec', 'NativeParseSpec',
           'ParseTwiceSpec', 'ParseEmptySpec')
