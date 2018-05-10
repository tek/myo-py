from amino import do, Do, __, Maybe, _

from chiasma.util.id import Ident

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.util.persist import store_json_state
from ribosome.compute.ribosome_api import Ribo

from myo.data.command import Command, HistoryEntry
from myo.components.command.data import CommandData
from myo.components.command.compute.tpe import CommandRibosome


def store_history() -> NS[CommandData, None]:
    return store_json_state('history', _.history)


@prog
@do(NS[CommandRibosome, None])
def push_history(cmd: Command, target: Maybe[Ident]) -> Do:
    entry = HistoryEntry(cmd, target)
    yield Ribo.modify_comp(__.append1.history(entry))
    yield Ribo.zoom_comp(store_history())


__all__ = ('push_history',)
