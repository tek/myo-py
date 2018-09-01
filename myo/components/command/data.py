from uuid import uuid4, UUID

from amino import Dat, Nil, Map, Path, List, Either, _, Maybe
from amino.list import replace_one

from myo.data.command import Command, HistoryEntry, RunningCommand, CommandConfig
from myo.output.data.report import ParseReport
from myo.output.config import LangConfig

from chiasma.util.id import Ident

from ribosome.nvim.scratch import ScratchBuffer
from ribosome.nvim.io.state import NS


class OutputData(Dat['OutputData']):

    @staticmethod
    def cons(
            report: ParseReport=None,
            scratch: ScratchBuffer=None,
            current: int=0,
    ) -> 'OutputData':
        return OutputData(
            Maybe.optional(report),
            Maybe.optional(scratch),
            current,
        )

    def __init__(
            self,
            report: Maybe[ParseReport],
            scratch: Maybe[ScratchBuffer],
            current: int,
    ) -> None:
        self.report = report
        self.scratch = scratch
        self.current = current


class CommandData(Dat['CommandData']):

    @staticmethod
    def cons(
            commands: List[Command]=Nil,
            command_configs: List[CommandConfig]=Nil,
            lang_configs: List[LangConfig]=Nil,
            logs: Map[Ident, Path]=Map(),
            uuid: UUID=None,
            history: List[HistoryEntry]=Nil,
            output: OutputData=None,
            running: List[RunningCommand]=Nil,
    ) -> 'CommandData':
        return CommandData(
            commands,
            command_configs,
            lang_configs,
            logs,
            uuid or uuid4(),
            history,
            output or OutputData.cons(),
            running,
        )

    def __init__(
            self,
            commands: List[Command],
            command_configs: List[CommandConfig],
            lang_configs: List[LangConfig],
            logs: Map[Ident, Path],
            uuid: UUID,
            history: List[HistoryEntry],
            output: OutputData,
            running: List[RunningCommand]=Nil,
    ) -> None:
        self.commands = commands
        self.command_configs = command_configs
        self.lang_configs = lang_configs
        self.logs = logs
        self.uuid = uuid
        self.history = history
        self.output = output
        self.running = running

    def command_by_ident(self, ident: Ident) -> Either[str, Command]:
        return self.commands.find(_.ident == ident).to_either(f'no command `{ident}`')

    def replace_command(self, cmd: Command) -> 'CommandData':
        return self.mod.commands(lambda cs: replace_one(cs, _.ident == cmd.ident, cmd)._value() | (lambda: cs.cat(cmd)))

    def log_by_ident(self, ident: Ident) -> Either[str, Path]:
        return self.logs.lift(ident).to_either(f'no log for `{ident}`')

    def log(self, ident: Ident, path: Path) -> 'CommandData':
        return self.append.logs((ident, path))


def running_command(ident: Ident) -> NS[CommandData, Command]:
    return NS.inspect(lambda a: a.running.find(lambda b: b.ident == ident).to_either(f'no running command `{ident}`'))


__all__ = ('CommandData',)
