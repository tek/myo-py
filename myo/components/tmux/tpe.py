from ribosome.compute.ribosome import Ribosome

from chiasma.data.tmux import TmuxData

from myo.env import Env
from myo.config.component import MyoComponent

TmuxRibosome = Ribosome[Env, MyoComponent, TmuxData]


__all__ = ('TmuxRibosome',)
