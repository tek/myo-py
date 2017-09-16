from amino import List, Just, Lists

from ribosome import NvimFacade

from myo.env import Env
from myo.state import MyoState


class Myo(MyoState):

    def __init__(self, vim: NvimFacade, plugins: List[str]=List()) -> None:
        core = 'myo.plugins.core'
        super().__init__(vim, Lists.wrap(plugins).cons(core))

    @property
    def init(self) -> Env:
        return Env(vim_facade=Just(self.vim))

__all__ = ('Myo',)
