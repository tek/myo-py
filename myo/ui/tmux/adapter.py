from myo.logging import Logging


class Adapter(Logging):

    def __init__(self, native) -> None:
        self.native = native

__all__ = ('Adapter',)
