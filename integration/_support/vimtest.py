from functools import wraps
from amino import env


def vimtest(f):
    @wraps(f)
    def wrapper(self):
        def go(vimtest):
            self.vim.amend_optionl('rtp', [vimtest])
            self.vim.cmd('source {}/plugin/*.vim'.format(vimtest))
            return f(self)
        env['VIMTEST_DIR'] % go
    return wrapper

__all__ = ('vimtest',)
