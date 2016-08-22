from integration._support.base import MyoPluginIntegrationSpec


class CmdSpec(MyoPluginIntegrationSpec):
    pass

    @property
    def _plugins(self):
        return super()._plugins.cat('myo.plugins.command')

__all__ = ('CmdSpec',)
