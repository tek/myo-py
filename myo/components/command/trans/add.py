from amino import do, Do, Maybe, List, Either, __, Boolean
from amino.state import State
from amino.dat import Dat
from amino.lenses.lens import lens
from amino.boolean import false

from ribosome.trans.api import trans

from myo.util import Ident
from myo.data.command import Command, SystemInterpreter, VimInterpreter, ShellInterpreter
from myo.env import Env


class AddVimCommandOptions(Dat['AddVimCommandOptions']):

    def __init__(
            self,
            line: Maybe[str],
            lines: Maybe[List[str]],
            silent: Maybe[Boolean],
            target: Maybe[Ident],
    ) -> None:
        self.line = line
        self.lines = lines
        self.silent = silent
        self.target = target


class AddSystemCommandOptions(Dat['AddSystemCommandOptions']):

    def __init__(
            self,
            line: Maybe[str],
            lines: Maybe[List[str]],
            target: Maybe[Ident],
    ) -> None:
        self.line = line
        self.lines = lines
        self.target = target


class AddShellCommandOptions(Dat['AddShellCommandOptions']):

    def __init__(
            self,
            line: Maybe[str],
            lines: Maybe[List[str]],
            target: Ident,
    ) -> None:
        self.line = line
        self.lines = lines
        self.target = target


def cons_vim_command(name: str, options: AddVimCommandOptions) -> Either[str, Command]:
    return Command(
        name,
        VimInterpreter(options.silent | false, options.target),
        options.lines.o(options.line / List),
        List('vim'),
    )


def cons_system_command(name: str, options: AddSystemCommandOptions) -> Either[str, Command]:
    return Command(name, SystemInterpreter(options.target), options.lines.o(options.line / List))


def cons_shell_command(name: str, options: AddShellCommandOptions) -> Either[str, Command]:
    return Command(name, ShellInterpreter(options.target), options.lines.o(options.line / List))


@trans.free.unit(trans.st)
@do(State[Env, None])
def add_vim_command(name: str, options: AddVimCommandOptions) -> Do:
    cmd = cons_vim_command(name, options)
    yield State.modify(lens.comp.commands.modify(__.cat(cmd)))


@trans.free.unit(trans.st)
@do(State[Env, None])
def add_system_command(name: str, options: AddSystemCommandOptions) -> Do:
    cmd = cons_system_command(name, options)
    yield State.modify(lens.comp.commands.modify(__.cat(cmd)))


@trans.free.unit(trans.st)
@do(State[Env, None])
def add_shell_command(name: str, options: AddShellCommandOptions) -> Do:
    cmd = cons_shell_command(name, options)
    yield State.modify(lens.comp.commands.modify(__.cat(cmd)))


__all__ = ('add_system_command', 'add_vim_command')
