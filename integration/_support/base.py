from pathlib import Path

from amino import List, Right

from ribosome.test import PluginIntegrationSpec
from ribosome.test.integration import ExternalIntegrationSpec

from myo.test.spec import Spec
from myo.logging import Logging

from integration._support.plugin import MyoSpecPlugin


class IntegrationCommon:

    @property
    def plugin_class(self):
        return Right(MyoSpecPlugin)

    @property
    def _prefix(self):
        return 'myo'

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self._set_vars()

    def _set_vars(self):
        self.vim.vars.set_p('config_path', str(self._config_path))
        self.vim.vars.set_p('plugins', self._plugins)

    @property
    def _config_path(self):
        return Path('/dev/null')

    @property
    def _plugins(self):
        return List()


class MyoIntegrationSpec(IntegrationCommon, ExternalIntegrationSpec):
    pass


class MyoPluginIntegrationSpec(IntegrationCommon, PluginIntegrationSpec, Spec,
                               Logging):

    def _pre_start(self):
        super()._pre_start()
        self.vim.cmd_sync('MyoStart')
        self._wait_for(lambda: self.vim.vars.p('started').is_just)
        self.vim.cmd('MyoPostStartup')

__all__ = ('MyoIntegrationSpec', 'MyoPluginIntegrationSpec')
