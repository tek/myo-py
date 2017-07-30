from functools import wraps
from amino import env


def vimtest(f):
    @wraps(f)
    def wrapper(self):
        def go(vimtest):
            self.vim.options.amend_l('rtp', [vimtest])
            self.vim.cmd('source {}/plugin/*.vim'.format(vimtest))
            return f(self)
        return env['VIMTEST_DIR'] / go | None
    return wrapper

__all__ = ('vimtest',)
