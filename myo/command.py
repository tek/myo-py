from tryp import List


class Command(object):

    def __init__(self, name: str, line: str):
        self.name = name
        self.line = line


class VimCommand(Command):
    pass


class ShellCommand(Command):
    pass


class Commands(object):

    def __init__(self, commands: List[Command]=List()) -> None:
        self.commands = commands

    def __add__(self, command: Command):
        return Commands(self.commands + [command])

__all__ = ['Commands', 'Command']
