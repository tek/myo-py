from integration._support.base import MyoIntegrationSpec

from amino.test.path import fixture_path
from amino import Map, Just, List, _
from amino.test import temp_file, later
from amino.lazy import lazy

from ribosome.test.integration import main_looped
from ribosome.machine.scratch import Mapping

from myo.command import Command
from myo.plugins.core.message import ParseOutput


class ParseHelpers:

    def _modifiable(self, val):
        self.vim.buffer.options('modifiable').should.contain(val)


class ParseSpec(MyoIntegrationSpec, ParseHelpers):

    @main_looped
    def native(self):
        cmd = Command(name='a', line='a', parser=Just('compiler'))
        fix = fixture_path('parse', 'err1')
        output = List.wrap(fix.read_text().splitlines())
        errorformat = List(
            '%AIn %f:%l',
            '%C  %.%#',
            '%+Z%.%#Error: %.%#'
        ).mk_string(',')
        self.vim.buffer.options.set('errorformat', errorformat)
        msg = ParseOutput(cmd, output, fix, Map())
        self.plugin.myo_start()
        self.root.send(msg)
        self._await()
        qf = self.vim.call('getqflist') | []
        qf.should_not.be.empty

    def twice(self):
        cmd = Command(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, List(), None, Map())
        self.plugin.myo_start()
        self.root.send_sync(msg)
        output_machine = self.root.sub[-1]
        self._modifiable(False)
        self.root.send_sync(Mapping(output_machine.uuid, 'q'))
        self._modifiable(True)
        self.root.send_sync(msg)
        self._modifiable(False)

_trace_len = 3
_line_count = _trace_len * 4 + 5


class ParseSpecBase(MyoIntegrationSpec):

    def _pre_start(self):
        super()._pre_start()
        self.vim.vars.set_p('jump_to_error', False)


class PythonParseSpec(ParseSpecBase):

    def _pre_start(self):
        super()._pre_start()
        self.vim.vars.set_p('output_reifier',
                            'py:myo.output.reifier.base.LiteralReifier')

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
        return List(
            'import functools',
            'def {}(a, b=1):'.format(self._python_func_name),
            '    return 1'
        )

    @property
    def _mk_trace(self):
        r = lambda: List.random_string(4)
        tmpl = '  File "{}", line 2, in {}'
        frame = lambda i: List(
            tmpl.format(self._file, self._python_func_name),
            '    {}()'.format(r())
        )
        t = List.range(_trace_len) // frame
        err = 'AttributeError: butt'
        return t.cat(err)

    def _parse(self, output, parse_opt=Map()):
        cmd = Command(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, output, None, parse_opt)
        self.plugin.myo_start()
        self.root.send_sync(msg)
        return output

    def _init(self, parse_opt=Map()):
        trace1 = self._mk_trace
        trace2 = self._mk_trace
        output = trace1 + trace2
        return self._parse(output, parse_opt)

    def _go(self, line_count=_line_count, parse_opt=Map()):
        output = self._init(parse_opt)
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.options('modifiable').should.contain(False)
        self.vim.buffer.content.should.have.length_of(line_count)

    def _check_jumped(self):
        self.vim.window.buffer.name.should.equal(str(self._file))
        self.vim.window.cursor.should.equal(List(2, 0))

    def jump(self):
        self._go()
        output_machine = self.root.sub[-1]
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self._check_jumped()

    def filter(self):
        filters = List('py:integration.core.parse_spec._filter1')
        self._go(_trace_len * 2 + 3, Map(output_filters=filters))

    def initial_pos(self):
        self.vim.vars.set_p('first_error',
                            ['py:integration.core.parse_spec._first_error'])
        self._go()
        self.vim.window.line.should.contain(_line_count - 1)

    def initial_pos_with_jump(self):
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.vars.set_p('first_error',
                            ['py:integration.core.parse_spec._first_error'])
        self._init()
        self._check_jumped()

    def default_jump(self):
        self.vim.vars.set_p('jump_to_error', True)
        self._init()
        self._check_jumped()

    def _syntax(self):
        from amino import log
        self.vim.vars.set_p('output_reifier', '')
        self.vim.vars.set_p('jump_to_error', True)
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        self._init()
        self._wait(3)
        log.info(self.vim.cmd_output('syntax').join_lines)
        self._check_jumped()


def _filter1(result):
    e = result.events
    e2 = e[:1] + e[1 + _trace_len * 2 + 2:]
    return result.set(events=e2)


def _first_error(a):
    return Just((_line_count - 1, 1))


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
            '[error]    {}()'.format(r()),
            '[error]    {}^'.format(' ' * l),
        )

    def _mk_scala_errors(self, count):
        return List.gen(count, lambda: self._mk_scala_error)

    def _parse(self, output):
        cmd = Command(name='a', line='a', langs=List('sbt'))
        msg = ParseOutput(cmd, output, None, Map())
        self.plugin.myo_start()
        self.root.send_sync(msg)

    def complete(self):
        self.vim.vars.set_p('output_reifier',
                            'myo.output.reifier.base.LiteralReifier')
        output = self._mk_scala_errors(1)
        self._parse(output)
        output_machine = self.root.sub[-1]
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.options('modifiable').should.contain(False)
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self.vim.window.buffer.name.should.equal(str(self._scala_file))
        self.vim.window.cursor.should.equal(List(3, 4))

    def filter_format(self):
        def check():
            c = self.vim.buffer.content
            c.should.have.length_of(6)
            c.head.should.contain('{}  3'.format(self._scala_file.name))
        filters = List('py:integration.core.parse_spec._filter')
        formatters = List('py:integration.core.parse_spec._format')
        trunc = 'py:integration.core.parse_spec._trunc'
        self.vim.vars.set_p('output_filters', filters)
        self.vim.vars.set_p('output_formatters', formatters)
        self.vim.vars.set_p('path_truncator', trunc)
        output = self._mk_scala_errors(4)
        self._parse(output)
        later(check)

    def _syntax(self):
        from amino import log
        self.vim.cmd_sync('hi Error cterm=bold ctermfg=1')
        output = self._mk_scala_errors(1)
        self._parse(output)
        self._wait(2)
        log.info(self.vim.cmd_output('syntax').join_lines)


def _filter(r):
    return r.modder.events(_[2:])


def _format(r):
    return r


def _trunc(path):
    return path.name

__all__ = ('ParseSpec',)
