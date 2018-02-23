from kallikrein.matchers.either import be_right
from kallikrein import kf

from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec
from ribosome.test.integration.klk import later

from myo.logging import Logging


class MyoPluginIntegrationSpec(AutoPluginIntegrationKlkSpec, Logging):

    def _pre_start(self) -> None:
        super()._pre_start()
        self.vim.cmd_once_defined('MyoStage1')
        later(kf(self.vim.vars.p, 'started').must(be_right))


class DefaultSpec(MyoPluginIntegrationSpec):

    def config_name(self) -> str:
        return 'config'

    def module(self) -> str:
        return 'myo'

    @property
    def plugin_prefix(self) -> str:
        return 'myo'


__all__ = ('MyoPluginIntegrationSpec', 'DefaultSpec')
