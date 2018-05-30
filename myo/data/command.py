from amino import List, Maybe, Dat, ADT, Boolean, Either, Map, Nil, Just, Nothing

from myo.util import Ident

from chiasma.util.id import IdentSpec, ensure_ident


class Interpreter(ADT['Interpreter']):
    pass


class VimInterpreter(Interpreter):

    @staticmethod
    def cons(silent: bool=False, target: IdentSpec=None) -> 'VimInterpreter':
        return VimInterpreter(Boolean(silent), Maybe.optional(target) / ensure_ident)

    def __init__(self, silent: Boolean, target: Maybe[Ident]) -> None:
        self.silent = silent
        self.target = target


class SystemInterpreter(Interpreter):

    @staticmethod
    def cons(target: IdentSpec=None) -> 'SystemInterpreter':
        return SystemInterpreter(Maybe.optional(target) / ensure_ident)

    def __init__(self, target: Maybe[Ident]) -> None:
        self.target = target


class ShellInterpreter(Interpreter):

    @staticmethod
    def cons(target: IdentSpec) -> 'ShellInterpreter':
        return ShellInterpreter(ensure_ident(target))

    def __init__(self, target: Ident) -> None:
        self.target = target


class Command(Dat['Command']):

    @staticmethod
    def cons(
            ident: IdentSpec,
            interpreter: Interpreter=None,
            lines: List[str]=Nil,
            langs: List[str]=Nil,
    ) -> 'Command':
        return Command(ensure_ident(ident), interpreter or SystemInterpreter.cons(), lines, langs)

    def __init__(self, ident: Ident, interpreter: Interpreter, lines: List[str], langs: List[str]) -> None:
        self.ident = ident
        self.interpreter = interpreter
        self.lines = lines
        self.langs = langs


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
           'TestLineParams', 'TestCommand', 'HistoryEntry', 'RunningCommand', 'Pid',)
