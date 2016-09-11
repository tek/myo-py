from myo.dispatch import Dispatcher

from ribosome.machine import Nop


class DummyDispatcher(Dispatcher):

    def can_run(self, cmd):
        return True

    def message(self, cmd, options):
        return Nop()

__all__ = ('DummyDispatcher',)
