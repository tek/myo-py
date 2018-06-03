from amino import do, Do

from ribosome.nvim.io.state import NS

from myo.components.command.data import CommandData
from myo.data.command import HistoryEntry, Command


def history_entry(index: int) -> NS[CommandData, HistoryEntry]:
    return NS.inspect_maybe(
        lambda s: s.history.lift(len(s.history) - 1 - index),
        lambda: f'no history entry for index `index`'
    )


@do(NS[CommandData, Command])
def most_recent_command() -> Do:
    entry = yield history_entry(0)
    return entry.cmd


__all__ = ('history_entry', 'most_recent_command',)
