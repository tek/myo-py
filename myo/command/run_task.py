from amino import ADT, Path, Dat

from myo.data.command import Command
from myo.ui.data.view import Pane


class RunTaskDetails(ADT['RunTaskDetails']):
    pass


class VimTaskDetails(RunTaskDetails):
    pass


class SystemTaskDetails(RunTaskDetails):
    pass


class UiSystemTaskDetails(RunTaskDetails):

    def __init__(self, pane: Pane) -> None:
        self.pane = pane


class UiShellTaskDetails(RunTaskDetails):

    def __init__(self, shell: Command, pane: Pane) -> None:
        self.shell = shell
        self.pane = pane


class RunTask(Dat['RunTask']):

    def __init__(self, command: Command, log: Path, details: RunTaskDetails) -> None:
        self.command = command
        self.log = log
        self.details = details


def is_system_task(task: RunTaskDetails) -> bool:
    return isinstance(task, (SystemTaskDetails, UiSystemTaskDetails))


__all__ = ('RunTaskDetails', 'VimTaskDetails', 'SystemTaskDetails', 'UiSystemTaskDetails', 'UiShellTaskDetails',
           'RunTask', 'is_system_task',)
