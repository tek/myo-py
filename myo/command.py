from tryp import List


class Command(object):
    pass


class VimCommand(Command):
    pass


class Commands(object):

    def __init__(self, commands: List[Command]=List()) -> None:
        self.commands = commands

__all__ = ['Commands', 'Command']
