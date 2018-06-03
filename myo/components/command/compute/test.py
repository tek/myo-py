from typing import TypeVar

from amino import do, Do, __, List, Nil, Nothing, Just
from amino.logging import module_log

from chiasma.util.id import StrIdent, ensure_ident_or_generate, IdentSpec

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N

from myo.components.command.data import CommandData
from myo.components.command.compute.run import run, RunCommandOptions
from myo.data.command import Command, SystemInterpreter
from myo.components.command.compute.vim_test import vim_test_line
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import test_pane, test_ui, test_langs

log = module_log()
D = TypeVar('D')
test_ident = StrIdent('<test>')


def cons_test_command(ui: str, target: IdentSpec) -> Command:
    effective_target = Nothing if ui == 'internal' else Just(ensure_ident_or_generate(target))
    return Command.cons(ident=test_ident, interpreter=SystemInterpreter(effective_target))


@do(NS[CommandData, None])
def update_test_command(lines: List[str], langs: List[str]) -> Do:
    ui = yield NS.lift(test_ui.value_or_default())
    target = yield NS.lift(test_pane.value_or_default())
    existing = yield NS.inspect(__.command_by_ident(test_ident))
    cmd = existing.get_or(cons_test_command, ui, target)
    global_langs = yield NS.lift(test_langs.value_or_default())
    updated_cmd = cmd.set.lines(lines).set.langs(global_langs + langs)
    log.debug(f'computed test command `{updated_cmd}`')
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
    yield run(test_ident, run_options)


__all__ = ('vim_test',)
