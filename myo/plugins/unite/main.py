from ribosome.machine import may_handle, handle
from ribosome.unite import UniteKind
from ribosome.machine.base import UnitTask
from ribosome.unite.data import UniteSyntax
from ribosome.unite.machine import UniteMachine, UniteTransitions

from amino import Map, List, _, __
from amino.lazy import lazy

from myo.plugins.unite.message import UniteHistory
from myo.state import MyoTransitions, MyoComponent
from myo.plugins.unite.data import UniteNames, HistorySource


class MyoUniteTransitions(UniteTransitions, MyoTransitions):

    def unite_cmd(self, cmd):
        args = ' '.join(self.msg.unite_args)
        self.vim.cmd('Unite {} {}'.format(cmd, args))

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

    @property
    def sources(self):
        return List(self.history_source)

    @lazy
    def run_action(self):
        return Map(name='run', handler=UniteNames.run, desc='run command')

    @property
    def actions(self):
        return List(self.run_action)

    @lazy
    def run_kind(self):
        return UniteKind(UniteNames.history, List(self.run_action))

    @property
    def kinds(self):
        return List(self.run_kind)

__all__ = ('Plugin',)
