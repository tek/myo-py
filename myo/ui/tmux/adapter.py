from myo.logging import Logging


class Adapter(Logging):

    def __init__(self, native) -> None:
        self.native = native

    def __repr__(self):
        return 'A({})'.format(self.native)

__all__ = ('Adapter',)
