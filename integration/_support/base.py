from pathlib import Path

from tryp import List, Right

from trypnv.test import VimIntegrationSpec, PluginIntegrationSpec

from myo.test.spec import Spec, TmuxSpec
from myo.logging import Logging
from myo.nvim_plugin import MyoNvimPlugin


class MyoIntegrationSpec(VimIntegrationSpec):
    pass


class MyoPluginIntegrationSpec(PluginIntegrationSpec, Spec, Logging):

    def _pre_start(self):
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
    def plugin_class(self):
        return Right(MyoNvimPlugin)

    @property
    def _plugins(self):
        return List()

    @property
    def _config_path(self):
        return Path('/dev/null')


class TmuxIntegrationSpec(MyoPluginIntegrationSpec, TmuxSpec):

    def _pre_start_neovim(self):
        super()._pre_start_neovim()
        self._setup_server()

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self.vim.set_pvar('tmux_socket', self.socket)
        id = self.session.windows[0].panes[0].id_i | -1
        wid = self.session.windows[0].id_i | -1
        self.vim.set_pvar('tmux_force_vim_pane_id', id)
        self.vim.set_pvar('tmux_force_vim_win_id', wid)

    def teardown(self):
        super().teardown()
        self._teardown_server()

__all__ = ('TmuxIntegrationSpec', 'MyoIntegrationSpec',
           'MyoPluginIntegrationSpec')
