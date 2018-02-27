from amino import ADT

from myo.data.command import Command
from myo.ui.data.view import Pane


class RunTask(ADT['RunTask']):
    pass


class VimTask(RunTask):
    pass


class SystemTask(RunTask):

    def __init__(self, command: Command) -> None:
        self.command = command


class UiSystemTask(RunTask):

    def __init__(self, command: Command, pane: Pane) -> None:
        self.command = command
        self.pane = pane


class UiShellTask(RunTask):

    def __init__(self, command: Command, shell: Command, pane: Pane) -> None:
        self.command = command
        self.shell = shell
        self.pane = pane


__all__ = ('RunTask', 'VimTask', 'SystemTask', 'UiSystemTask', 'UiShellTask')
