from integration._support.base import MyoPluginIntegrationSpec


class CmdSpecConf:

    @property
    def _plugins(self):
        return super()._plugins.cat('myo.plugins.command')


class CmdSpec(CmdSpecConf, MyoPluginIntegrationSpec):
    pass

__all__ = ('CmdSpec', 'CmdSpecConf')
