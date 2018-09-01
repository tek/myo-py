from typing import TypeVar

from amino import do, Do, Maybe, List, Either, __, Boolean, Nil
from amino.dat import Dat
from amino.lenses.lens import lens
from amino.boolean import false

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome import Ribosome
from ribosome.compute.ribosome_api import Ribo

from myo.util import Ident
from myo.data.command import Command, SystemInterpreter, VimInterpreter, ShellInterpreter
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData

A = TypeVar('A')
CommandRiboState = NS[Ribosome[Env, MyoComponent, CommandData], A]


class AddVimCommandOptions(Dat['AddVimCommandOptions']):

    def __init__(
            self,
            ident: Maybe[Ident],
            line: Maybe[str],
            lines: Maybe[List[str]],
            silent: Maybe[Boolean],
            target: Maybe[Ident],
            langs: Maybe[List[str]],
    ) -> None:
        self.ident = ident
        self.line = line
        self.lines = lines
        self.silent = silent
        self.target = target
        self.langs = langs


class AddSystemCommandOptions(Dat['AddSystemCommandOptions']):

    def __init__(
            self,
            ident: Maybe[Ident],
            line: Maybe[str],
            lines: Maybe[List[str]],
            target: Maybe[Ident],
            langs: Maybe[List[str]],
    ) -> None:
        self.ident = ident
        self.line = line
        self.lines = lines
        self.target = target
        self.langs = langs


class AddShellCommandOptions(Dat['AddShellCommandOptions']):

    def __init__(
            self,
            ident: Maybe[Ident],
            line: Maybe[str],
            lines: Maybe[List[str]],
            target: Ident,
            langs: Maybe[List[str]],
    ) -> None:
        self.ident = ident
        self.line = line
        self.lines = lines
        self.target = target
        self.langs = langs


def cons_vim_command(options: AddVimCommandOptions) -> Either[str, Command]:
    return Command.cons(
        options.ident | Ident.generate,
        VimInterpreter(options.silent | false, options.target),
        options.lines.o(options.line / List) | Nil,
        options.langs | List('vim'),
    )


def cons_system_command(options: AddSystemCommandOptions) -> Either[str, Command]:
    return Command.cons(
        options.ident | Ident.generate,
        SystemInterpreter(options.target),
        options.lines.o(options.line / List) | Nil,
        options.langs | Nil,
    )


def cons_shell_command(options: AddShellCommandOptions) -> Command:
    return Command.cons(
        options.ident | Ident.generate,
        ShellInterpreter(options.target),
        options.lines.o(options.line / List) | Nil,
        options.langs | Nil,
    )


@prog.unit
@do(NS[Ribosome[Env, MyoComponent, CommandData], None])
def add_vim_command(options: AddVimCommandOptions) -> Do:
    cmd = cons_vim_command(options)
    yield Ribo.modify_comp(lens.commands.modify(__.cat(cmd)))


@prog.unit
@do(NS[Ribosome[Env, MyoComponent, CommandData], None])
def add_system_command(options: AddSystemCommandOptions) -> Do:
    cmd = cons_system_command(options)
    yield Ribo.modify_comp(lens.commands.modify(__.cat(cmd)))


@prog.unit
@do(NS[Ribosome[Env, MyoComponent, CommandData], None])
def add_shell_command(options: AddShellCommandOptions) -> Do:
    cmd = cons_shell_command(options)
    yield Ribo.modify_comp(lens.commands.modify(__.cat(cmd)))


__all__ = ('add_system_command', 'add_vim_command')
