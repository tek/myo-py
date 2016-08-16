from tryp import Path, __

from trypnv.record import list_field, field, maybe_field

from myo.record import Record, Named
from myo.ui.tmux.util import ident_field, Ident


class Command(Named):
    line = field(str)
    log_path = maybe_field(Path)


class VimCommand(Command):
    pass


class ShellCommand(Command):
    shell = ident_field()


class Shell(ShellCommand):
    target = ident_field()


class Commands(Record):
    commands = list_field()
    history = list_field()

    def __add__(self, command: Command):
        return self.append1.commands(command)

    def __getitem__(self, ident: Ident):
        return self.commands.find(__.has_ident(ident))

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(map(repr, self.commands))
        )

    def shell(self, name):
        pred = lambda a: isinstance(a, Shell) and a.name == name
        return self.commands.find(pred)

    def add_history(self, uuid):
        return self.append1.history(uuid)

__all__ = ('Commands', 'Command')
