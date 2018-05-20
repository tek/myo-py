from ribosome.compute.ribosome import Ribosome

from myo.components.tmux.data import TmuxData

from myo.env import Env
from myo.config.component import MyoComponent

TmuxRibosome = Ribosome[Env, MyoComponent, TmuxData]


__all__ = ('TmuxRibosome',)
