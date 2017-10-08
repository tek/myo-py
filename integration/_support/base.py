from amino import List, Right

from kallikrein.matchers.either import be_right
from kallikrein import kf

from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec, ExternalIntegrationKlkSpec
from ribosome.test.integration.klk import later

from myo.test.spec import Spec
from myo.logging import Logging
from myo.nvim_plugin import MyoNvimPlugin


class IntegrationCommon:

    @property
    def plugin_class(self):
        return Right(MyoNvimPlugin)

    @property
    def _prefix(self):
        return 'myo'

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self._set_vars()

    def _set_vars(self):
        self.vim.vars.set_p('components', self._plugins)

    @property
    def _plugins(self):
        return List()


class MyoIntegrationSpec(IntegrationCommon, ExternalIntegrationKlkSpec):

    def _start_plugin(self):
        self.plugin.stage_1()
        self._wait(.05)
        self._wait_for(lambda: self.vim.vars.p('started').present)


class MyoPluginIntegrationSpec(IntegrationCommon, AutoPluginIntegrationKlkSpec, Spec, Logging):

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.cmd_once_defined('MyoStage1')
        later(kf(self.vim.vars.p, 'started').must(be_right))


class DefaultSpec(MyoPluginIntegrationSpec):

    def config_name(self) -> str:
        return 'config'

    def module(self) -> str:
        return 'myo.nvim_plugin'

    @property
    def plugin_prefix(self) -> str:
        return 'myo'


__all__ = ('MyoIntegrationSpec', 'MyoPluginIntegrationSpec', 'DefaultSpec')
