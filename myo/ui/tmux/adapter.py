from libtmux.common import TmuxRelationalObject

from myo.logging import Logging


class Adapter(Logging):

    def __init__(self, native) -> None:
        if not isinstance(native, TmuxRelationalObject):
            raise Exception(
                'passed {!r} to {}'.format(native, self.__class__.__name__))
        self.native = native

    def __repr__(self):
        return 'A({})'.format(self.native)

__all__ = ('Adapter',)
