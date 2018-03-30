from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines
from kallikrein.matchers.length import have_length
from kallikrein.matchers.tuple import tupled
from kallikrein.matchers import contain

from chiasma.test.tmux_spec import tmux_spec_socket

from amino.test import fixture_path
from amino import List, do, Do

from ribosome.test.klk import kn
from ribosome.nvim.api.ui import current_buffer_content, send_input, buffers
from ribosome.nvim.api.variable import variable_set_prefixed
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.data import Buffer
from ribosome.nvim.api.command import nvim_command

from integration._support.python_parse import events
from integration._support.spec import TmuxDefaultSpec


class PythonParseSpec(TmuxDefaultSpec):
    '''
    parse a python traceback $parse
    '''

    def parse(self) -> Expectation:
        pane = 'paney'
        file = fixture_path('tmux', 'python_parse', 'trace')
        @do(NvimIO[List[Buffer]])
        def run() -> Do:
            yield variable_set_prefixed('vim_tmux_pane', 0)
            yield variable_set_prefixed('tmux_socket', tmux_spec_socket)
            yield variable_set_prefixed('auto_jump', 0)
            yield nvim_command('MyoStage1')
            yield self.json_cmd_sync('MyoCreatePane', name=pane, layout='root')
            yield self.json_cmd_sync('MyoOpenPane', pane)
            yield self.json_cmd_sync('MyoLine', pane=pane, lines=List(f'cat {file}'), langs=List('python'))
            yield nvim_command('MyoParse')
            self._wait(1)
            lines = yield current_buffer_content()
            send_input('q').unsafe(self.vim)
            self._wait(.5)
            bufs = yield buffers()
            return lines, bufs
        return kn(self.vim, run).must(contain(tupled(2)((have_lines(events), have_length(1)))))


__all__ = ('PythonParseSpec',)
