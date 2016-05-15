from fn import _

import pyrsistent

from trypnv.data import field
from trypnv.record import Record, list_field


class Command(pyrsistent.PRecord):
    name = field(str)
    line = field(str)


class VimCommand(Command):
    pass


class ShellCommand(Command):
    pass


class Commands(Record):
    commands = list_field()

    def __add__(self, command: Command):
        return self.append('commands', [command])

    def __getitem__(self, name):
        return self.commands.find(_.name == name)

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(map(repr, self.commands))
        )

__all__ = ('Commands', 'Command')
