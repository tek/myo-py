from ribosome.data.plugin_state import PluginState

from myo.settings import MyoSettings
from myo.env import Env
from myo.config.component import MyoComponent

MyoPluginState = PluginState[MyoSettings, Env, MyoComponent]

__all__ = ('MyoPluginState',)
