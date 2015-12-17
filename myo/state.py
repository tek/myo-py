from trypnv import Machine, PluginStateMachine
from trypnv.nvim import HasNvim

from myo.nvim import NvimFacade
from myo.logging import Logging

from tryp import List


class MyoComponent(Machine, HasNvim, Logging):

    def __init__(self, name: str, vim: NvimFacade) -> None:
        Machine.__init__(self, name)
        HasNvim.__init__(self, vim)


class MyoState(PluginStateMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, plugins: List[str]) -> None:
        self.vim = vim
        PluginStateMachine.__init__(self, 'myo', plugins)
        HasNvim.__init__(self, vim)


__all__ = ['MyoComponent', 'MyoState']
