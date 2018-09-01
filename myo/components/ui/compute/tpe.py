from ribosome.compute.ribosome import Ribosome

from myo.env import Env
from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData

UiRibosome = Ribosome[Env, MyoComponent, UiData]


__all__ = ('UiRibosome',)
