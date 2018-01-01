from amino import List, Maybe, Dat, ADT, Boolean, Either, Map

from myo.util import Ident


class Interpreter(ADT['Interpreter']):
    pass


class VimInterpreter(Interpreter):

    def __init__(self, silent: Boolean) -> None:
        self.silent = silent


class SystemInterpreter(Interpreter):

    def __init__(self, target: Maybe[Ident]) -> None:
        self.target = target


class ShellInterpreter(Interpreter):

    def __init__(self, target: Ident) -> None:
        self.target = target


class Command(Dat['Command']):

    def __init__(self, ident: Ident, interpreter: Interpreter, lines: List[str]) -> None:
        self.ident = ident
        self.interpreter = interpreter
        self.lines = lines


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


__all__ = ('Command', 'Interpreter', 'VimInterpreter', 'SystemInterpreter', 'ShellInterpreter', 'Execute',
           'TestLineParams', 'TestCommand')
