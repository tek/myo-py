from ribosome.test import VimIntegrationSpec


class CmdSpecConf:

    @property
    def _plugins(self):
        return super()._plugins.cat('myo.plugins.command')


class CmdSpec(CmdSpecConf, VimIntegrationSpec):
    pass

__all__ = ('CmdSpec', 'CmdSpecConf')
