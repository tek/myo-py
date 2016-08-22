from integration._support.base import MyoIntegrationSpec

from amino.test.path import fixture_path
from amino import Map, Just, List

from ribosome.test.integration import main_looped

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
        frame = lambda i: List('  File "/path/{}"'.format(i), 'call()')
        t = List.range(3) // frame
        err = 'AttributeError: butt'
        return t.cat(err)

    def python(self):
        trace1 = self._mk_trace
        trace2 = self._mk_trace

__all__ = ('ParseSpec',)
