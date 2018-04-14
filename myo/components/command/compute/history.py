from amino import do, Do, __, Maybe, _

from chiasma.util.id import Ident
from amino.lenses.lens import lens

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.config.resources import Resources
from ribosome.config.component import ComponentData
from ribosome.util.persist import store_json_state

from myo.data.command import Command, HistoryEntry
from myo.env import Env
from myo.settings import MyoSettings
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData


def store_history() -> NS[Resources[ComponentData[Env, CommandData], MyoSettings, MyoComponent], None]:
    return store_json_state('history', _.comp.history)


@prog
@do(NS[Resources[MyoSettings, ComponentData[Env, CommandData], MyoComponent], None])
def push_history(cmd: Command, target: Maybe[Ident]) -> Do:
    entry = HistoryEntry(cmd, target)
    yield NS.modify(lens.data.comp.modify(__.append1.history(entry)))
    yield store_history()


__all__ = ('push_history',)
