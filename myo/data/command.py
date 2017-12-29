from amino import List, Maybe, Dat, ADT

from myo.util import Ident


class Interpreter(ADT['Interpreter']):
    pass


class VimInterpreter(Interpreter):
    pass


class SystemInterpreter(Interpreter):
    pass


class ShellInterpreter(Interpreter):
    pass


class Command(Dat['Command']):

    def __init__(self, name: str, interpreter: Interpreter, lines: List[str], target: Maybe[Ident]) -> None:
        self.name = name
        self.interpreter = interpreter
        self.lines = lines
        self.target = target

__all__ = ('Command',)
