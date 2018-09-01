from ribosome.compute.ribosome import Ribosome

from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData

CommandRibosome = Ribosome[Env, MyoComponent, CommandData]


__all__ = ('CommandRibosome',)
