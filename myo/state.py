from ribosome import Machine, NvimFacade, RootMachine
from ribosome.nvim import HasNvim
from ribosome.machine import ModularMachine, Transitions

from myo.logging import Logging
from myo.env import Env


class MyoComponent(ModularMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        Machine.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class MyoState(RootMachine, Logging):
    _data_type = Env

    @property
    def title(self):
        return 'myo'


class MyoTransitions(Transitions, HasNvim):

    def __init__(self, machine, *a, **kw):
        Transitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
