from chiasma.test.tmux_spec import TmuxSpec

from ribosome.test.integration.klk import AutoPluginIntegrationKlkSpec, VimIntegrationKlkSpec


class DefaultSpec(AutoPluginIntegrationKlkSpec):

    def plugin_prefix(self) -> str:
        return 'myo'


class ExternalSpec(VimIntegrationKlkSpec):

    @property
    def plugin_name(self) -> str:
        return 'myo'

    def plugin_prefix(self) -> str:
        return 'myo'


class TmuxDefaultSpec(TmuxSpec, DefaultSpec):

    def __init__(self) -> None:
        TmuxSpec.__init__(self)
        DefaultSpec.__init__(self)

    def setup(self) -> None:
        TmuxSpec.setup(self)
        DefaultSpec.setup(self)

    def teardown(self) -> None:
        TmuxSpec.teardown(self)
        DefaultSpec.teardown(self)


__all__ = ('DefaultSpec', 'ExternalSpec', 'TmuxDefaultSpec')
