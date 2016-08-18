from tryp.test.path import fixture_path, base_dir
from tryp import List

from myo.plugins.command.util import assemble_vim_test_line

from integration._support.base import MyoIntegrationSpec
from integration._support.vimtest import vimtest


class VimTestSpec(MyoIntegrationSpec):

    @vimtest
    def vim_test_line(self):
        fname = fixture_path('tmux', 'vim_test', 'test.py')
        self.vim.cmd('noswapfile edit {}'.format(fname))
        self.vim.cursor(5, 0)
        base = base_dir().parent
        target = '{} -k test_something'.format(fname.relative_to(base))
        assemble_vim_test_line(self.vim).should.contain(List(target))

__all__ = ('VimTestSpec',)
