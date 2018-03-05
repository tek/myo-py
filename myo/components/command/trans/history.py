from amino import do, Do, __, Maybe, _

from chiasma.util.id import Ident
from amino.boolean import false
from amino.lenses.lens import lens

from ribosome.trans.api import trans
from ribosome.nvim.io import NS
from ribosome.trans.persist import store_json_state
from ribosome.config.config import Resources
from ribosome.dispatch.component import ComponentData

from myo.data.command import Command, HistoryEntry
from myo.env import Env
from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData


def store_history() -> NS[Resources[ComponentData[Env, CommandData], MyoSettings, MyoComponent], None]:
    return store_json_state('history', _.comp.history)


@trans.free.result(trans.st)
@do(NS[Resources[ComponentData[Env, CommandData], MyoSettings, MyoComponent], None])
def push_history(cmd: Command, target: Maybe[Ident]) -> Do:
    entry = HistoryEntry(cmd, target)
    yield NS.modify(lens.data.comp.modify(__.append1.history(entry)))
    yield store_history()


__all__ = ('push_history',)
