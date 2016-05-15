from pathlib import Path

from tryp.test import fixture_path

from tryp import List
from trypnv.test import IntegrationSpec as TrypnvIntegrationSpec
from trypnv.test import VimIntegrationSpec as TrypnvVimIntegrationSpec

from myo.test.spec import Spec, TmuxSpec
from myo.logging import Logging


class IntegrationSpec(TrypnvIntegrationSpec):
    pass


class VimIntegrationSpec(TrypnvVimIntegrationSpec, Spec, Logging):

    def setup(self):
        super().setup()
        self._pre_start()
        self.vim.cmd('MyoStart')
        self._wait_for(lambda: self.vim.pvar('started').is_just)
        self.vim.cmd('MyoPostStartup')

    @property
    def _prefix(self):
        return 'myo'

    def _pre_start_neovim(self):
        self._setup_plugin()

    def _post_start_neovim(self):
        self._set_vars()

    def _set_vars(self):
        self.vim.set_pvar('config_path', str(self._config_path))
        self.vim.set_pvar('plugins', self._plugins)

    def _setup_plugin(self):
        self._rplugin_path = fixture_path(
            'nvim_plugin', 'rplugin', 'python3', 'myo_nvim.py')
        self._handlers = [
            {
                'sync': 1,
                'name': 'MyoStart',
                'type': 'command',
                'opts': {'nargs': 0}
            },
            {
                'sync': 0,
                'name': 'MyoPostStartup',
                'type': 'command',
                'opts': {'nargs': 0}
            },
            {
                'sync': 0,
                'name': 'MyoVimCommand',
                'type': 'command',
                'opts': {'nargs': '+'}
            },
            {
                'sync': 0,
                'name': 'BufEnter',
                'type': 'autocmd',
                'opts': {'pattern': '*'}
            },
            {
                'sync': 0,
                'name': 'MyoTest',
                'type': 'command',
                'opts': {'nargs': 0}
            },
            {
                'sync': 0,
                'name': 'MyoTmuxCreateSession',
                'type': 'command',
                'opts': {'nargs': '*'}
            },
            {
                'sync': 0,
                'name': 'MyoTmuxSpawnSession',
                'type': 'command',
                'opts': {'nargs': 1}
            },
            {
                'sync': 0,
                'name': 'MyoTmuxCreateLayout',
                'type': 'command',
                'opts': {'nargs': '*'}
            },
            {
                'sync': 0,
                'name': 'MyoTmuxCreatePane',
                'type': 'command',
                'opts': {'nargs': '*'}
            },
            {
                'sync': 0,
                'name': 'MyoTmuxOpenPane',
                'type': 'command',
                'opts': {'nargs': '+'}
            },
        ]

    @property
    def _plugins(self):
        return List()

    def _pre_start(self):
        pass

    @property
    def _config_path(self):
        return Path('/dev/null')


class TmuxIntegrationSpec(VimIntegrationSpec, TmuxSpec):

    def _pre_start_neovim(self):
        super()._pre_start_neovim()
        self._setup_server()

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self.vim.set_pvar('tmux_socket', self.socket)
        id = self.session.windows[0].panes[0]._pane_id[1:]
        self.vim.set_pvar('tmux_force_vim_pane_id', id)

    def teardown(self):
        super().teardown()
        self._teardown_server()

__all__ = ('IntegrationSpec', 'VimIntegrationSpec', 'TmuxIntegrationSpec')
