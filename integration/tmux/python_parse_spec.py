from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines

from chiasma.test.tmux_spec import tmux_spec_socket

from amino.test import fixture_path
from amino import List

from ribosome.nvim.api import current_buffer_content
from ribosome.test.klk import kn
from ribosome.test.integration.klk import later

from integration._support.python_parse import events
from integration._support.spec import TmuxDefaultSpec


class PythonParseSpec(TmuxDefaultSpec):
    '''
    parse a python traceback $parse
    '''

    def parse(self) -> Expectation:
        pane = 'paney'
        file = fixture_path('tmux', 'python_parse', 'trace')
        self.vim.vars.set_p('vim_tmux_pane', 0)
        self.vim.vars.set_p('tmux_socket', tmux_spec_socket)
        self.vim.cmd_sync('MyoStage1')
        self.json_cmd_sync('MyoCreatePane', name=pane, layout='root')
        self.json_cmd_sync('MyoOpenPane', pane)
        self.json_cmd_sync('MyoLine', pane=pane, lines=List(f'cat {file}'), langs=List('python'))
        self.cmd_sync('MyoParse')
        self._wait(1)
        return kn(current_buffer_content(), self.vim).must(have_lines(events))


__all__ = ('PythonParseSpec',)
