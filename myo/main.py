from pathlib import Path  # type: ignore

from toolz.itertoolz import cons

from tryp import List

from myo.nvim import NvimFacade
from myo.env import Env
from myo.state import MyoState


class Myo(MyoState):

    def __init__(
            self,
            vim: NvimFacade,
            config_path: Path,
            plugins: List[str],
    ) -> None:
        self._config_path = config_path
        core = 'myo.plugins.core'
        MyoState.__init__(self, vim, List.wrap(cons(core, plugins)))

    def init(self):
        return Env(  # type: ignore
            config_path=self._config_path,
        )

__all__ = ['Myo']
