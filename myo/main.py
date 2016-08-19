from pathlib import Path

from toolz.itertoolz import cons

from amino import List

from ribosome import NvimFacade

from myo.env import Env
from myo.state import MyoState


class Myo(MyoState):

    def __init__(
            self,
            vim: NvimFacade,
            config_path: Path=Path('/dev/null'),
            plugins: List[str]=List(),
    ) -> None:
        self._config_path = config_path
        core = 'myo.plugins.core'
        super().__init__(vim, List.wrap(cons(core, plugins)))

    @property
    def init(self):
        return Env(  # type: ignore
            config_path=self._config_path,
        )

__all__ = ('Myo',)
