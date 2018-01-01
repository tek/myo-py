from amino import _, List, Nil, Either, Maybe
from amino.dat import Dat

from myo.util import Ident
from myo.data.command import Command, TestLineParams


class Env(Dat['Env']):

    @staticmethod
    def cons(
            commands: List[Command]=Nil,
            test_params: TestLineParams=None,
    ) -> 'Env':
        return Env(commands, test_params)

    def __init__(
            self,
            commands: List[Command],
            test_params: Maybe[TestLineParams],
    ) -> None:
        self.commands = commands
        self.test_params = test_params

    def command_by_ident(self, ident: Ident) -> Either[str, Command]:
        return self.commands.find(_.ident == ident).to_either(f'no command `{ident}`')

__all__ = ('Env',)
