from pathlib import Path

from amino import List, Right

from kallikrein.matchers.either import be_right
from kallikrein import k, kf

from ribosome.test.integration.klk import PluginIntegrationKlkSpec, ExternalIntegrationKlkSpec
from ribosome.test.integration.klk import later

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


class MyoIntegrationSpec(IntegrationCommon, ExternalIntegrationKlkSpec):

    def _start_plugin(self):
        self.plugin.start_plugin()
        self._wait(.05)
        self._wait_for(lambda: self.vim.vars.p('started').present)


class MyoPluginIntegrationSpec(IntegrationCommon, PluginIntegrationKlkSpec, Spec, Logging):

    def __init__(self) -> None:
        super().__init__()
        self.log_format = '{message}'

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.cmd_sync('MyoStart')
        later(kf(self.vim.vars.p, 'started').must(be_right))

__all__ = ('MyoIntegrationSpec', 'MyoPluginIntegrationSpec')
