from fn import _

from trypnv.record import list_field, field

from tryp import Maybe, Empty

from myo.record import Record
from myo.ui.tmux.pane import contains_pane_ident


class Command(Record):
    name = field(str)
    line = field(str)


class VimCommand(Command):
    pass


class ShellCommand(Command):
    pass


class Shell(ShellCommand):
    target = field(Maybe, initial=Empty(), invariant=contains_pane_ident)


class Commands(Record):
    commands = list_field()

    def __add__(self, command: Command):
        return self.append1.commands(command)

    def __getitem__(self, name):
        return self.commands.find(_.name == name)

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(map(repr, self.commands))
        )

    def shell(self, name):
        pred = lambda a: isinstance(a, Shell) and a.name == name
        return self.commands.find(pred)

__all__ = ('Commands', 'Command')
