from amino import Map, List

from ribosome.unite import UniteKind, UniteSource
from ribosome.unite.machine import UniteMachine
from ribosome.trans.api import trans
from ribosome.dispatch.component import Component

from myo.components.unite.message import UniteHistory, UniteCommands
from myo.components.unite.data import UniteNames, HistorySource, CommandsSource

history_source = HistorySource()
commands_source = CommandsSource()
sources = List(history_source, commands_source)
run_action = Map(name='run', handler=UniteNames.run, desc='run command')
delete_action = Map(name='delete', handler=UniteNames.delete, desc='delete command')
command_kind = UniteKind(UniteNames.command, List(run_action))
history_command_kind = UniteKind(UniteNames.history_command, List(run_action, delete_action))
kinds = List(command_kind, history_command_kind)


class MyoUniteTransitions(Component):

    def unite_cmd(self, cmd: str) -> None:
        args = ' '.join(self.msg.unite_args)
        self.vim.cmd('Unite {} {}'.format(cmd, args))

    @trans.msg.unit(UniteCommands)
    def commands(self, msg: UniteCommands) -> None:
        self.unite_cmd(UniteNames.commands)

    @trans.msg.unit(UniteHistory)
    def history(self, msg: UniteHistory) -> None:
        self.unite_cmd(UniteNames.history)


class Unite(UniteMachine):

    @property
    def sources(self) -> List[UniteSource]:
        return sources

    @property
    def kinds(self) -> List[UniteKind]:
        return kinds


__all__ = ('Unite',)
