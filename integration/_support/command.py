from integration._support.base import MyoPluginIntegrationSpec

from amino import __


class CmdSpecConf:

    @property
    def _plugins(self):
        return super()._plugins.cat('myo.plugins.command')

    @property
    def _last(self):
        return (lambda: self.vim.vars.pd('last_command') // __.get('name'))

    def _create_command(self, name, line, **opt):
        self.json_cmd_sync('MyoShellCommand {}'.format(name), line=line, **opt)
        self._wait(.1)

    def _run_command(self, name, **opt):
        self.json_cmd_sync('MyoRun {}'.format(name), **opt)
        self._wait(.1)


class CmdSpec(CmdSpecConf, MyoPluginIntegrationSpec):
    pass

__all__ = ('CmdSpec', 'CmdSpecConf')
