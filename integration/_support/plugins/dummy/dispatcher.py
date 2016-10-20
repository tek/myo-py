from amino import Empty

from myo.dispatch import Dispatcher
from myo.plugins.command.message import CommandExecuted


class DummyDispatcher(Dispatcher):

    def can_run(self, cmd):
        return True

    def message(self, cmd, options):
        return CommandExecuted(cmd, Empty())

__all__ = ('DummyDispatcher',)
