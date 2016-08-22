from integration._support.base import MyoPluginIntegrationSpec
from integration._support.command import CmdSpec

from myo.test.spec import TmuxSpecBase


class TmuxIntegrationSpec(MyoPluginIntegrationSpec, TmuxSpecBase):

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

    @property
    def _plugins(self):
        self._debug = True
        return super()._plugins.cons('myo.plugins.tmux')


class DefaultLayoutSpec(TmuxIntegrationSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.set_pvar('tmux_use_defaults', True)


class TmuxCmdSpec(TmuxIntegrationSpec, CmdSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.set_pvar('tmux_use_defaults', True)
        self.vim.set_pvar('tmux_vim_width', 10)
        self.vim.set_pvar('tmux_watcher_interval', 0.1)

__all__ = ('TmuxIntegrationSpec', 'DefaultLayoutSpec', 'TmuxCmdSpec')
