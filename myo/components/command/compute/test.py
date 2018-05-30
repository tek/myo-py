from typing import TypeVar

from amino import do, Do, __, List, Nil
from amino.logging import module_log

from chiasma.util.id import StrIdent

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.data import CommandData
from myo.components.command.compute.run import run_command, RunCommandOptions
from myo.data.command import Command, SystemInterpreter
from myo.components.command.compute.vim_test import vim_test_line
from myo.components.command.compute.tpe import CommandRibosome

log = module_log()
D = TypeVar('D')
test_ident = StrIdent('<test>')


def cons_test_command() -> Command:
    return Command.cons(ident=test_ident, interpreter=SystemInterpreter.cons())


@do(NS[CommandData, None])
def update_test_command(lines: List[str], langs: List[str]) -> Do:
    existing = yield NS.inspect(__.command_by_ident(test_ident))
    cmd = existing | cons_test_command
    updated_cmd = cmd.set.lines(lines).set.langs(langs)
    yield NS.modify(__.replace_command(updated_cmd))


@do(NS[CommandRibosome, List[str]])
def vim_test_lines() -> Do:
    line = yield vim_test_line()
    return List(line)


@prog
@do(NS[CommandRibosome, None])
def vim_test_command(langs: List[str]) -> Do:
    lines = yield vim_test_lines()
    yield Ribo.zoom_comp(update_test_command(lines, langs))


@prog.do(None)
def vim_test(run_options: RunCommandOptions) -> Do:
    yield vim_test_command(run_options.langs.get_or_strict(Nil))
    yield run_command(test_ident, run_options)


__all__ = ('vim_test',)
