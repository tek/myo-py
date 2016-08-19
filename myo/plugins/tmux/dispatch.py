from functools import singledispatch  # type: ignore

from ribosome.machine import Error

from myo.dispatch import Dispatcher
from myo.command import ShellCommand, Shell
from myo.plugins.tmux.message import (TmuxRunCommand, TmuxRunLineInShell,
                                       TmuxRunShell)
from myo.plugins.command.main import RunInShell


@singledispatch
def convert_message(msg, options):
    return Error('invalid message for tmux dispatch: {}'.format(msg))


@convert_message.register(RunInShell)
def _convert_run_in_shell(cmd, options):
    return TmuxRunLineInShell(cmd.shell, options)


@convert_message.register(Shell)  # type: ignore
def _convert_shell(cmd, options):
    return TmuxRunShell(cmd, options)


@convert_message.register(ShellCommand)  # type: ignore
def _convert_shell_command(cmd, options):
    return TmuxRunCommand(cmd, options)


class TmuxDispatcher(Dispatcher):

    def can_run(self, cmd):
        return isinstance(cmd, (ShellCommand, RunInShell))

    def message(self, cmd, options):
        return convert_message(cmd, options)

__all__ = ('TmuxDispatcher',)
