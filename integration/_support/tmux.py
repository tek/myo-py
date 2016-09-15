from integration._support.base import MyoPluginIntegrationSpec
from integration._support.command import CmdSpec

from amino.test import later

from myo.test.spec import TmuxSpecBase


class TmuxIntegrationSpec(MyoPluginIntegrationSpec, TmuxSpecBase):

    def _pre_start_neovim(self):
        super()._pre_start_neovim()
        self._setup_server()

    def _post_start_neovim(self):
        super()._post_start_neovim()
        self.vim.vars.set_p('tmux_socket', self.socket)
        id = self.session.windows[0].panes[0].id_i | -1
        wid = self.session.windows[0].id_i | -1
        self.vim.vars.set_p('tmux_force_vim_pane_id', id)
        self.vim.vars.set_p('tmux_force_vim_win_id', wid)

    def teardown(self):
        super().teardown()
        self._teardown_server()

    @property
    def _plugins(self):
        self._debug = True
        return super()._plugins.cons('myo.plugins.tmux')

    def _create_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxCreatePane {}'.format(name), **kw)

    def _open_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxOpen {}'.format(name), **kw)
        self._wait(.1)

    def _pane_count(self, count: int):
        return later(lambda: self._panes.should.have.length_of(count))


class DefaultLayoutSpec(TmuxIntegrationSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', True)


class TmuxCmdSpec(TmuxIntegrationSpec, CmdSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', True)
        self.vim.vars.set_p('tmux_vim_width', 10)
        self.vim.vars.set_p('tmux_watcher_interval', 0.1)

__all__ = ('TmuxIntegrationSpec', 'DefaultLayoutSpec', 'TmuxCmdSpec')
