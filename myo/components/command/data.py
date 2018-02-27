from uuid import uuid4, UUID

from amino import Dat, Nil, Map, Path, List, Either, _

from myo.data.command import Command

from chiasma.util.id import Ident


class CommandData(Dat['CommandData']):

    @staticmethod
    def cons(
            commands: List[Command]=Nil,
            logs: Map[Ident, Path]=Map(),
            uuid: UUID=None,
    ) -> 'CommandData':
        return CommandData(
            commands,
            logs,
            uuid or uuid4(),
        )

    def __init__(self, commands: List[Command], logs: Map[Ident, Path], uuid: UUID) -> None:
        self.commands = commands
        self.logs = logs
        self.uuid = uuid

    def command_by_ident(self, ident: Ident) -> Either[str, Command]:
        return self.commands.find(_.ident == ident).to_either(f'no command `{ident}`')

    def log_by_ident(self, ident: Ident) -> Either[str, Path]:
        return self.logs.lift(ident).to_either(f'no log for `{ident}`')

    def log(self, ident: Ident, path: Path) -> 'CommandData':
        return self.append.logs((ident, path))


__all__ = ('CommandData',)
