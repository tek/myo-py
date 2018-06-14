from amino import do, Do, __, Maybe, _, List
from amino.lenses.lens import lens

from chiasma.util.id import Ident

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.util.persist import store_json_state, load_json_state
from ribosome.compute.ribosome_api import Ribo

from myo.data.command import Command, HistoryEntry
from myo.components.command.data import CommandData
from myo.components.command.compute.tpe import CommandRibosome


def store_history() -> NS[CommandData, None]:
    return store_json_state('history', _.history)


def restore_history() -> NS[CommandData, None]:
    return load_json_state('history', lens.history)


@prog
@do(NS[CommandRibosome, None])
def push_history(cmd: Command, target: Maybe[Ident]) -> Do:
    entry = HistoryEntry(cmd, target)
    yield Ribo.modify_comp(__.append1.history(entry))
    yield Ribo.zoom_comp(store_history())


@prog
def history() -> NS[CommandRibosome, List[HistoryEntry]]:
    return Ribo.inspect_comp(lambda a: a.history)


__all__ = ('push_history', 'history', 'read_history', 'store_history',)
