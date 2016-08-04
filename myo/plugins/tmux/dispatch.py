from myo.dispatch import Dispatcher
from myo.command import ShellCommand, Shell
from myo.plugins.tmux.messages import (TmuxRunCommand, TmuxRunLineInShell,
                                       TmuxRunShell)
from myo.plugins.command import RunInShell


class TmuxDispatcher(Dispatcher):

    def can_run(self, cmd):
        return isinstance(cmd, ShellCommand) or isinstance(cmd, RunInShell)

    def message(self, cmd, options):
        if isinstance(cmd, RunInShell):
            return TmuxRunLineInShell(cmd.shell, options)
        elif isinstance(cmd, Shell):
            return TmuxRunShell(cmd, options)
        else:
            return TmuxRunCommand(cmd, options)

__all__ = ('TmuxDispatcher',)
