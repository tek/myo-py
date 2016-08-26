from integration._support.base import MyoIntegrationSpec

from amino.test.path import fixture_path
from amino import Map, Just, List

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

    @property
    def _mk_trace(self):
        r = lambda: List.random_string(4)
        tmpl = '  File "/path/{}", line 10, in {}'
        frame = lambda i: List(tmpl.format(i, r()), '    {}()'.format(r()))
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
        self.vim.window.set_cursor(4).attempt()
        self.root.send_sync(Mapping(output_machine.uuid, '%cr%'))
        self.vim.buffer.content.should.contain(output[-1])
        self.vim.buffer.option('modifiable').should.contain(False)

__all__ = ('ParseSpec',)
