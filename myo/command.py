from amino import Path, __, Just

from ribosome.record import list_field, field, maybe_field, bool_field

from myo.record import Record, Named
from myo.ui.tmux.util import ident_field, Ident


class Command(Named):
    line = field(str)
    log_path = maybe_field(Path)
    parser = maybe_field(str)
    transient = bool_field()
    langs = list_field()


class VimCommand(Command):
    pass


class ShellCommand(Command):
    shell = ident_field()


class Shell(ShellCommand):
    target = ident_field()


class Commands(Record):
    commands = list_field()
    history = list_field()
    transient_cmd = maybe_field(Command)

    def __add__(self, command: Command):
        return self.append1.commands(command)

    def __getitem__(self, ident: Ident):
        return (
            self.commands.find(__.has_ident(ident))
            .to_either('no command with ident {}'.format(ident))
        )

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(map(repr, self.commands))
        )

    def shell(self, ident):
        pred = lambda a: isinstance(a, Shell) and a.has_ident(ident)
        return self.commands.find(pred)

    def add_history(self, uuid):
        return self.append1.history(uuid)

    def transient_command(self, cmd):
        return self.set(transient_cmd=Just(cmd))

    def latest_command(self):
        def fetch(ident):
            return (
                self.transient_cmd.filter(__.has_ident(ident))
                .or_else(lambda: self[ident])
            )
        return self.history.head // fetch

__all__ = ('Commands', 'Command')
