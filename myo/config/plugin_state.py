from ribosome.data.plugin_state import PluginState

from myo.env import Env
from myo.config.component import MyoComponent

MyoPluginState = PluginState[Env, MyoComponent]

__all__ = ('MyoPluginState',)
