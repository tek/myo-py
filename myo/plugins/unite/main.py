from ribosome.machine import may_handle
from ribosome.unite import UniteKind
from ribosome.unite.machine import UniteMachine, UniteTransitions

from amino import Map, List
from amino.lazy import lazy

from myo.plugins.unite.message import UniteHistory, UniteCommands
from myo.state import MyoTransitions, MyoComponent
from myo.plugins.unite.data import UniteNames, HistorySource, CommandsSource


class MyoUniteTransitions(UniteTransitions, MyoTransitions):

    def unite_cmd(self, cmd):
        args = ' '.join(self.msg.unite_args)
        self.vim.cmd('Unite {} {}'.format(cmd, args))

    @may_handle(UniteCommands)
    def commands(self):
        self.unite_cmd(UniteNames.commands)

    @may_handle(UniteHistory)
    def history(self):
        self.unite_cmd(UniteNames.history)


class Plugin(UniteMachine, MyoComponent):
    Transitions = MyoUniteTransitions

    def __init__(self, *a, **kw):
        UniteMachine.__init__(self)
        MyoComponent.__init__(self, *a, **kw)

    @lazy
    def history_source(self):
        return HistorySource()

    @lazy
    def commands_source(self):
        return CommandsSource()

    @property
    def sources(self):
        return List(self.history_source, self.commands_source)

    @lazy
    def run_action(self):
        return Map(name='run', handler=UniteNames.run, desc='run command')

    @property
    def actions(self):
        return List(self.run_action)

    @lazy
    def run_kind(self):
        return UniteKind(UniteNames.command, List(self.run_action))

    @property
    def kinds(self):
        return List(self.run_kind)

__all__ = ('Plugin',)
