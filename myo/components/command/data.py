from uuid import uuid4, UUID

from amino import Dat, Nil, Map, Path, List, Either, _, Maybe
from amino.list import replace_one

from myo.data.command import Command, HistoryEntry
from myo.output.data import OutputLine, Location

from chiasma.util.id import Ident

from ribosome.nvim.scratch import ScratchBuffer


class OutputData(Dat['OutputData']):

    @staticmethod
    def cons(
            lines: List[OutputLine]=Nil,
            locations: List[Location]=Nil,
            scratch: ScratchBuffer=None,
            current: int=0,
    ) -> 'OutputData':
        return OutputData(
            lines,
            locations,
            Maybe.optional(scratch),
            current,
        )

    def __init__(
            self,
            lines: List[OutputLine],
            locations: List[Location],
            scratch: Maybe[ScratchBuffer],
            current: int,
    ) -> None:
        self.lines = lines
        self.locations = locations
        self.scratch = scratch
        self.current = current


class CommandData(Dat['CommandData']):

    @staticmethod
    def cons(
            commands: List[Command]=Nil,
            logs: Map[Ident, Path]=Map(),
            uuid: UUID=None,
            history: List[HistoryEntry]=Nil,
            output: OutputData=None,
    ) -> 'CommandData':
        return CommandData(
            commands,
            logs,
            uuid or uuid4(),
            history,
            output or OutputData.cons(),
        )

    def __init__(
            self,
            commands: List[Command],
            logs: Map[Ident, Path],
            uuid: UUID,
            history: List[HistoryEntry],
            output: OutputData,
    ) -> None:
        self.commands = commands
        self.logs = logs
        self.uuid = uuid
        self.history = history
        self.output = output

    def command_by_ident(self, ident: Ident) -> Either[str, Command]:
        return self.commands.find(_.ident == ident).to_either(f'no command `{ident}`')

    def replace_command(self, cmd: Command) -> 'CommandData':
        return self.mod.commands(lambda cs: replace_one(cs, _.ident == cmd.ident, cmd)._value() | (lambda: cs.cat(cmd)))

    def log_by_ident(self, ident: Ident) -> Either[str, Path]:
        return self.logs.lift(ident).to_either(f'no log for `{ident}`')

    def log(self, ident: Ident, path: Path) -> 'CommandData':
        return self.append.logs((ident, path))


__all__ = ('CommandData',)
