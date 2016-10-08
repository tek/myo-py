import time

from libtmux.common import TmuxRelationalObject

from amino import List

from myo.logging import Logging


class Adapter(Logging):

    def __init__(self, native) -> None:
        if not isinstance(native, TmuxRelationalObject):
            raise Exception(
                'passed {!r} to {}'.format(native, self.__class__.__name__))
        self.native = native

    def __repr__(self):
        return 'A({})'.format(self.native)

    def cmd(self, *a):
        start = time.time()
        c = self.native.cmd(*a)
        if c.stderr:
            self.log.error(List.wrap(c.stderr).join_lines)
        self.log.ddebug(
            'tmux cmd `{}` took {:.4f}'.format(' '.join(a),
                                               time.time() - start))
        return c.stdout

    def cmd_async(self, *a):
        self.native.cmd(*a)

__all__ = ('Adapter',)
