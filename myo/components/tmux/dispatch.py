from functools import singledispatch

from ribosome.machine.messages import Error

from myo.dispatch import Dispatcher
from myo.command import ShellCommand, CommandJob
from myo.components.tmux.message import TmuxRunCommand, TmuxRebootCommand
from myo.components.command.main import Reboot


@singledispatch
def convert_message(msg, options):
    return Error('invalid message for tmux dispatch: {}'.format(msg))


@convert_message.register(ShellCommand)
def _convert_shell_command(cmd, options):
    return TmuxRunCommand(CommandJob(command=cmd, options=options), options)


@convert_message.register(CommandJob)
def _convert_command_job(cmd, options):
    return TmuxRunCommand(cmd, options)


@convert_message.register(Reboot)
def _convert_command_reboot(cmd, options):
    return TmuxRebootCommand(cmd.job, options)


class TmuxDispatcher(Dispatcher):

    def can_run(self, cmd):
        return isinstance(cmd, (ShellCommand, CommandJob, Reboot))

    def message(self, cmd, options):
        return convert_message(cmd, options)

__all__ = ('TmuxDispatcher',)
