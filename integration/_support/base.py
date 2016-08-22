from pathlib import Path

from amino import List, Right

from ribosome.test import PluginIntegrationSpec
from ribosome.test.integration import ExternalIntegrationSpec

from myo.test.spec import Spec
from myo.logging import Logging
from myo.nvim_plugin import MyoNvimPlugin


class IntegrationCommon:

    @property
    def plugin_class(self):
        return Right(MyoNvimPlugin)


class MyoIntegrationSpec(IntegrationCommon, ExternalIntegrationSpec):
    pass


class MyoPluginIntegrationSpec(IntegrationCommon, PluginIntegrationSpec, Spec,
                               Logging):

    def _pre_start(self):
        super()._pre_start()
        self.vim.cmd_sync('MyoStart')
        self._wait_for(lambda: self.vim.pvar('started').is_just)
        self.vim.cmd('MyoPostStartup')

    @property
    def _prefix(self):
        return 'myo'

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self._set_vars()

    def _set_vars(self):
        self.vim.set_pvar('config_path', str(self._config_path))
        self.vim.set_pvar('plugins', self._plugins)

    @property
    def _plugins(self):
        return List()

    @property
    def _config_path(self):
        return Path('/dev/null')

__all__ = ('MyoIntegrationSpec', 'MyoPluginIntegrationSpec')
