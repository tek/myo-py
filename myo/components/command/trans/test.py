from typing import TypeVar

from amino import do, Do, __, List
from amino.lenses.lens import lens

from chiasma.util.id import StrIdent

from ribosome.nvim.io import NS
from ribosome.trans.api import trans
from ribosome.trans.action import TransM
from ribosome.dispatch.component import ComponentData
from ribosome.config.config import Resources
from ribosome import ribo_log

from myo.components.command.data import CommandData
from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.components.command.trans.run import run_command, RunCommandOptions
from myo.data.command import Command, SystemInterpreter
from myo.components.command.trans.vim_test import vim_test_line

D = TypeVar('D')
test_ident = StrIdent('<test>')


def cons_test_command() -> Command:
    return Command.cons(ident=test_ident, interpreter=SystemInterpreter.cons())


@do(NS[CommandData, None])
def update_test_line(lines: List[str]) -> Do:
    existing = yield NS.inspect(__.command_by_ident(test_ident))
    cmd = existing | cons_test_command
    updated_cmd = cmd.set.lines(lines)
    yield NS.modify(__.replace_command(updated_cmd))


@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], List[str]])
def vim_test_lines() -> Do:
    line = yield vim_test_line()
    return List(line)


@trans.free.result(trans.st)
@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], None])
def vim_test_command() -> Do:
    lines = yield vim_test_lines()
    yield update_test_line(lines).zoom(lens.data.comp)


@trans.free.do()
@do(TransM)
def vim_test(run_options: RunCommandOptions) -> Do:
    yield vim_test_command.m
    yield run_command(test_ident, run_options).m

__all__ = ('vim_test',)
