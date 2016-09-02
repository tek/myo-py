from integration._support.base import MyoIntegrationSpec

from amino.test.path import fixture_path
from amino import Map, Just, List, _
from amino.test import temp_file
from amino.lazy import lazy

from ribosome.test.integration import main_looped
from ribosome.machine.scratch import Mapping

from myo.command import Command
from myo.plugins.core.message import ParseOutput


class ParseSpec(MyoIntegrationSpec):

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
        self.vim.buffer.set_option('errorformat', errorformat)
        msg = ParseOutput(cmd, output, fix, Map())
        self.plugin.myo_start()
        self.root.send(msg)
        self._await()
        qf = self.vim.call('getqflist') | []
        qf.should_not.be.empty


class PythonParseSpec(MyoIntegrationSpec):

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
        t = List.range(3) // frame
        err = 'AttributeError: butt'
        return t.cat(err)

    def python(self):
        trace1 = self._mk_trace
        trace2 = self._mk_trace
        output = trace1 + trace2
        cmd = Command(name='a', line='a', langs=List('python'))
        msg = ParseOutput(cmd, output, None, Map())
        self.plugin.myo_start()
        self.root.send_sync(msg)
        output_machine = self.root.sub[-1]
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.option('modifiable').should.contain(False)
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self.vim.window.buffer.name.should.equal(str(self._file))
        self.vim.window.cursor.should.equal(List(2, 0))


class SbtParseSpec(MyoIntegrationSpec):

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
    def _mk_scala_trace(self):
        r = lambda: List.random_string(4)
        tmpl = '[error] {}:{}: butt'
        return List(
            tmpl.format(self._scala_file, self._line),
            '[error]    {}()'.format(r()),
            '[error]    ^',
        )

    def sbt(self):
        output = self._mk_scala_trace
        cmd = Command(name='a', line='a', langs=List('sbt'))
        msg = ParseOutput(cmd, output, None, Map())
        self.plugin.myo_start()
        self.root.send_sync(msg)
        output_machine = self.root.sub[-1]
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.option('modifiable').should.contain(False)
        self.vim.window.set_cursor(4)
        self.root.send_sync(Mapping(output_machine.uuid, '%cr%'))
        self.vim.windows.should.have.length_of(2)
        self.vim.window.buffer.name.should.equal(str(self._scala_file))
        self.vim.window.cursor.should.equal(List(3, 4))

__all__ = ('ParseSpec',)
