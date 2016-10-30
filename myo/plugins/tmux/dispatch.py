from functools import singledispatch  # type: ignore

from ribosome.machine import Error

from myo.dispatch import Dispatcher
from myo.command import ShellCommand, Shell, CommandJob
from myo.plugins.tmux.message import (TmuxRunCommand, TmuxRunShell,
                                      TmuxRunTransient)


@singledispatch
def convert_message(msg, options):
    return Error('invalid message for tmux dispatch: {}'.format(msg))


@convert_message.register(Shell)
def _convert_shell(cmd, options):
    return TmuxRunShell(CommandJob(command=cmd), options)


@convert_message.register(ShellCommand)
def _convert_shell_command(cmd, options):
    return TmuxRunCommand(CommandJob(command=cmd), options)


@convert_message.register(CommandJob)
def _convert_command_job(cmd, options):
    return TmuxRunCommand(cmd, options)


class TmuxDispatcher(Dispatcher):

    def can_run(self, cmd):
        return isinstance(cmd, (ShellCommand, CommandJob))

    def message(self, cmd, options):
        return convert_message(cmd, options)

__all__ = ('TmuxDispatcher',)
