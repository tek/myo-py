from amino.test.path import fixture_path, base_dir

from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from myo.components.command.util import assemble_vim_test_line

from integration._support.base import MyoIntegrationSpec
from integration._support.vimtest import vimtest


class VimTestSpec(MyoIntegrationSpec):
    '''run vim-test's cmdline assembler according to the file type $vim_test_line
    '''

    @vimtest
    def vim_test_line(self) -> Expectation:
        fname = fixture_path('tmux', 'vim_test', 'test.py')
        self.vim.cmd('noswapfile edit {}'.format(fname))
        self.vim.cursor(5, 0)
        base = base_dir().parent
        relname = fname.relative_to(base)
        target = f'py.test {relname}::Namespace::test_something'
        return k(assemble_vim_test_line(self.vim)).must(be_right(target))

__all__ = ('VimTestSpec',)
