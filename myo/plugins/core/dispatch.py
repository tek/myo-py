from myo.dispatch import Dispatcher
from myo.command import VimCommand

from trypnv.nvim import HasNvim


class VimDispatcher(Dispatcher, HasNvim):

    def can_run(self, cmd):
        return isinstance(cmd, VimCommand)

    def message(self, cmd):
        return RunVimCommand(cmd)

__all__ = ('VimDispatcher',)
