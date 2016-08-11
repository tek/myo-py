from trypnv import Machine, PluginStateMachine
from trypnv.nvim import HasNvim
from trypnv.machine import ModularMachine, Transitions

from myo.nvim import NvimFacade
from myo.logging import Logging
from myo.env import Env

from tryp import List


class MyoComponent(ModularMachine, HasNvim, Logging):

    def __init__(self, name: str, vim: NvimFacade, parent=None) -> None:
        Machine.__init__(self, name, parent)
        HasNvim.__init__(self, vim)


class MyoState(PluginStateMachine, HasNvim, Logging):
    _data_type = Env

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        HasNvim.__init__(self, vim)
        PluginStateMachine.__init__(self, 'myo', plugins)


class MyoTransitions(Transitions, HasNvim):

    def __init__(self, machine, *a, **kw):
        Transitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
