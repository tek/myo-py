from typing import TypeVar

from amino import do, Do, __, List, Nil, Nothing, Just, Either, Right
from amino.logging import module_log

from chiasma.util.id import StrIdent, IdentSpec, ensure_ident

from ribosome.nvim.io.state import NS
from ribosome.compute.api import prog
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.data import CommandData
from myo.components.command.compute.run import run, RunCommandOptions
from myo.data.command import Command, SystemInterpreter, ShellInterpreter
from myo.components.command.compute.vim_test import vim_test_line
from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import test_pane, test_ui, test_langs, test_shell

log = module_log()
D = TypeVar('D')
test_ident = StrIdent('<test>')


@do(Either[str, Command])
def cons_test_pane_command(ui: str, target: IdentSpec) -> Do:
    effective_target = yield Right(Nothing) if ui == 'internal' else ensure_ident(target).map(Just)
    return Command.cons(ident=test_ident, interpreter=SystemInterpreter(effective_target))


@do(Either[str, Command])
def cons_test_shell_command(ui: str, shell: IdentSpec) -> Do:
    ident = yield ensure_ident(shell)
    return Command.cons(ident=test_ident, interpreter=ShellInterpreter(ident))


def cons_test_command(ui: str, shell: Either[str, IdentSpec], target: IdentSpec) -> Command:
    return shell.cata(
        lambda e: cons_test_pane_command(ui, target),
        lambda a: cons_test_shell_command(ui, a),
    )


@do(NS[CommandData, None])
def update_test_command(lines: List[str], langs: List[str]) -> Do:
    ui = yield NS.lift(test_ui.value_or_default())
    shell = yield NS.lift(test_shell.value)
    target = yield NS.lift(test_pane.value_or_default())
    existing = yield NS.inspect(__.command_by_ident(test_ident))
    cmd = yield existing.cata(
        lambda e: NS.e(cons_test_command(ui, shell, target)),
        NS.pure,
    )
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
