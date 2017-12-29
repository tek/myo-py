from amino import do, Do, Maybe, List, Either, __
from amino.state import State
from amino.dat import Dat
from amino.lenses.lens import lens

from ribosome.trans.api import trans

from myo import Env
from myo.util import Ident
from myo.data.command import Command, SystemInterpreter


class AddSystemCommandOptions(Dat['AddCommandOptions']):

    def __init__(
            self,
            line: Maybe[str],
            lines: Maybe[List[str]],
            target: Maybe[Ident],
    ) -> None:
        self.line = line
        self.lines = lines
        self.target = target


def cons_system_command(name: str, options: AddSystemCommandOptions) -> Either[str, Command]:
    return Command(name, SystemInterpreter, options.lines.o(options.line / List), options.target)


@trans.free.unit(trans.st)
@do(State[Env, None])
def add_system_command(name: str, options: AddSystemCommandOptions) -> Do:
    cmd = cons_system_command(name, options)
    yield State.modify(lens.comp.commands.modify(__.cat(cmd)))


__all__ = ('add_system_command',)
