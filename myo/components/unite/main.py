from typing import Any

from amino import Map, List

from ribosome.machine.transition import may_handle
from ribosome.unite import UniteKind, UniteSource
from ribosome.unite.machine import UniteMachine, UniteTransitions
from ribosome.machine.state import Component, ComponentMachine
from ribosome.nvim import NvimFacade
from ribosome.machine.machine import Machine

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


class MyoUniteTransitions(UniteTransitions, Component):

    def unite_cmd(self, cmd: str) -> None:
        args = ' '.join(self.msg.unite_args)
        self.vim.cmd('Unite {} {}'.format(cmd, args))

    @may_handle(UniteCommands)
    def commands(self) -> None:
        self.unite_cmd(UniteNames.commands)

    @may_handle(UniteHistory)
    def history(self) -> None:
        self.unite_cmd(UniteNames.history)


class Unite(UniteMachine, ComponentMachine):

    def __init__(self, vim: NvimFacade, title: str, parent: Machine) -> None:
        UniteMachine.__init__(self)
        ComponentMachine.__init__(self, vim, MyoUniteTransitions, title, parent)

    @property
    def sources(self) -> List[UniteSource]:
        return sources

    @property
    def kinds(self) -> List[UniteKind]:
        return kinds


__all__ = ('Unite',)
