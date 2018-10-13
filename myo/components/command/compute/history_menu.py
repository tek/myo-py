from amino import do, Do, Map
from amino.logging import module_log

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo
from ribosome.util.menu.data import MenuLine, MenuQuitWith, MenuUnit, Menu, MenuConfig
from ribosome.util.menu.auto.run import auto_menu, selected_menu_lines
from ribosome.util.menu.auto.data import AutoS, AutoState
from ribosome.util.menu.run import run_menu_prog
from ribosome.compute.prog import Prog

from myo.components.command.compute.tpe import CommandRibosome
from myo.components.command.compute.run import run_command
from myo.data.command import HistoryEntry
from myo.components.command.data import CommandData

log = module_log()


@do(AutoS)
def history_menu_selected() -> Do:
    items = yield selected_menu_lines()
    return items.head.cata_f(
        lambda a: MenuQuitWith(run_command(a.meta.cmd)),
        lambda: MenuUnit(),
    )


@do(NS[CommandRibosome, Menu[AutoState[None, HistoryEntry, None], HistoryEntry, None]])
def setup_history_menu() -> Do:
    history = yield Ribo.inspect_comp(lambda a: a.history)
    lines = history.map(
        lambda a: MenuLine.cons(f'[{a.cmd.ident.str}] {a.cmd.lines.head.get_or_strict("")}', a)
    )
    return auto_menu(
        None,
        lines,
        MenuConfig.cons('myo command history', insert=False),
        Map({'<cr>': history_menu_selected}),
    )


@prog.do(None)
def history_menu() -> Do:
    menu = yield Ribo.lift(setup_history_menu(), CommandData)
    yield run_menu_prog(menu)
    yield Prog.unit


__all__ = ('history_menu',)
