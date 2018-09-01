from amino import List, Maybe, Dat, ADT, Either, Map, Nil, Nothing, do, Do, Just

from myo.util import Ident
from myo.output.main import ParseConfig

from chiasma.util.id import IdentSpec, ensure_ident_or_generate, optional_ident, StrIdent


class Interpreter(ADT['Interpreter']):
    pass


class VimInterpreter(Interpreter):

    @staticmethod
    @do(Either[str, 'VimInterpreter'])
    def cons(silent: bool=False, target: IdentSpec=None) -> Do:
        ident = yield optional_ident(target)
        return VimInterpreter(silent, ident)

    @staticmethod
    def default() -> 'VimInterpreter':
        return VimInterpreter(False, Nothing)

    def __init__(self, silent: bool, target: Maybe[Ident]) -> None:
        self.silent = silent
        self.target = target


class SystemInterpreter(Interpreter):

    @staticmethod
    @do(Either[str, 'SystemInterpreter'])
    def cons(target: IdentSpec=None) -> Do:
        ident = yield optional_ident(target)
        return SystemInterpreter(ident)

    @staticmethod
    def str(target: str) -> 'SystemInterpreter':
        return SystemInterpreter(Just(StrIdent(target)))

    def __init__(self, target: Maybe[Ident]) -> None:
        self.target = target


class ShellInterpreter(Interpreter):

    @staticmethod
    @do(Either[str, 'ShellInterpreter'])
    def cons(target: IdentSpec) -> Do:
        ident = yield optional_ident(target)
        return ShellInterpreter(ident)

    @staticmethod
    def str(target: str) -> 'ShellInterpreter':
        return ShellInterpreter(StrIdent(target))

    def __init__(self, target: Ident) -> None:
        self.target = target


class CommandConfig(Dat['CommandConfig']):

    @staticmethod
    def cons(
            ident: IdentSpec,
            parsers: List[str]=None,
            output_filter: List[str]=None,
            output_first_error: str=None,
            output_path_formatter: str=None,
            output_reporter: str=None,
            output_syntax: str=None,
    ) -> 'CommandConfig':
        return CommandConfig(
            ensure_ident_or_generate(ident),
            Maybe.optional(parsers),
            Maybe.optional(output_filter),
            Maybe.optional(output_first_error),
            Maybe.optional(output_path_formatter),
            Maybe.optional(output_reporter),
            Maybe.optional(output_syntax),
        )

    def __init__(
            self,
            ident: Ident,
            parsers: Maybe[List[str]],
            output_filter: Maybe[List[str]],
            output_first_error: Maybe[str],
            output_path_formatter: Maybe[str],
            output_reporter: Maybe[str],
            output_syntax: Maybe[str],
    ) -> None:
        self.ident = ident
        self.parsers = parsers
        self.output_filter = output_filter
        self.output_first_error = output_first_error
        self.output_path_formatter = output_path_formatter
        self.output_reporter = output_reporter
        self.output_syntax = output_syntax

    @property
    def parse(self) -> ParseConfig:
        return ParseConfig(
            self.parsers.get_or_strict(Nil),
            self.output_filter.get_or_strict(Nil),
            self.output_first_error,
            self.output_path_formatter,
            self.output_reporter,
            self.output_syntax,
        )


class Command(Dat['Command']):

    @staticmethod
    def cons(
            ident: IdentSpec,
            interpreter: Interpreter=None,
            lines: List[str]=Nil,
            langs: List[str]=Nil,
            signals: List[str]=Nil,
            config: CommandConfig=None,
            history: bool=True,
    ) -> 'Command':
        return Command(
            ensure_ident_or_generate(ident),
            interpreter or SystemInterpreter(Nothing),
            lines,
            langs,
            signals,
            Maybe.optional(config),
            history
        )

    def __init__(
            self,
            ident: Ident,
            interpreter: Interpreter,
            lines: List[str],
            langs: List[str],
            signals: List[str],
            config: Maybe[CommandConfig],
            history: bool,
    ) -> None:
        self.ident = ident
        self.interpreter = interpreter
        self.lines = lines
        self.langs = langs
        self.signals = signals
        self.config = config
        self.history = history


class Execute(Dat['Execute']):

    def __init__(self, command: Ident) -> None:
        self.command = command


class TestLineParams(Dat['TestLineParams']):

    def __init__(
            self,
            line: str,
            shell: Either[str, str],
            target: Either[str, str],
            langs: List[str],
            options: Map[str, str],
    ) -> None:
        self.line = line
        self.shell = shell
        self.target = target
        self.langs = langs
        self.options = options


class TestCommand(Dat['TestCommand']):

    def __init__(self, command: Command, params: TestLineParams) -> None:
        self.command = command
        self.params = params


class HistoryEntry(Dat['HistoryEntry']):

    @staticmethod
    def cons(cmd: Command, target: Ident=None) -> 'HistoryEntry':
        return HistoryEntry(cmd, Maybe.optional(target))

    def __init__(self, cmd: Command, target: Maybe[Ident]) -> None:
        self.cmd = cmd
        self.target = target


class Pid(Dat['Pid']):

    def __init__(self, value: int) -> None:
        self.value = value


class RunningCommand(Dat['RunningCommand']):

    def __init__(self, ident: Ident, pid: Maybe[Pid], system: bool) -> None:
        self.ident = ident
        self.pid = pid
        self.system = system


__all__ = ('Command', 'Interpreter', 'VimInterpreter', 'SystemInterpreter', 'ShellInterpreter', 'Execute',
           'TestLineParams', 'TestCommand', 'HistoryEntry', 'RunningCommand', 'Pid', 'CommandConfig',)
