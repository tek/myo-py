from ribosome import NvimFacade, RootMachine
from ribosome.nvim import HasNvim

from ribosome.machine.state import SubMachine, SubTransitions
from ribosome.machine import MachineBase

from myo.logging import Logging
from myo.env import Env


class MyoComponent(Logging, SubMachine, HasNvim):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        MachineBase.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class MyoState(Logging, RootMachine):
    _data_type = Env

    @property
    def title(self):
        return 'myo'


class MyoTransitions(Logging, SubTransitions, HasNvim):

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
