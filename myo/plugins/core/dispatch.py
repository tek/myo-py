from myo.dispatch import Dispatcher
from myo.command import VimCommand
from myo.plugins.core.message import RunVimCommand

from ribosome.nvim import HasNvim


class VimDispatcher(Dispatcher, HasNvim):

    def can_run(self, cmd):
        return isinstance(cmd, VimCommand)

    def message(self, cmd, options):
        return RunVimCommand(cmd, options)

__all__ = ('VimDispatcher',)
