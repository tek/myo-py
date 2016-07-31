from myo.dispatch import Dispatcher
from myo.command import ShellCommand
from myo.plugins.tmux.messages import TmuxRunCommand


class TmuxDispatcher(Dispatcher):

    def can_run(self, cmd):
        return isinstance(cmd, ShellCommand)

    def message(self, cmd, options):
        return TmuxRunCommand(cmd, options)

__all__ = ('TmuxDispatcher',)
