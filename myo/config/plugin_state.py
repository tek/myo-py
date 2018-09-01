from ribosome.data.plugin_state import PluginState

from myo.env import Env
from myo.config.component import MyoComponent

MyoState = PluginState[Env, MyoComponent]

__all__ = ('MyoState',)
