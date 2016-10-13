from integration._support.base import (MyoPluginIntegrationSpec,
                                       MyoIntegrationSpec)
from integration._support.command import CmdSpecConf

from amino.test import later
from amino import _, __, Map, Maybe

from myo.test.spec import TmuxSpecBase
from myo.plugins.tmux.message import TmuxCreateLayout, TmuxCreatePane
from myo.plugins.tmux import TmuxOpen


class TmuxIntegrationSpecBase(TmuxSpecBase):

    def _pre_start_neovim(self):
        super()._pre_start_neovim()
        self._debug = True
        self._setup_server()

    def _post_start_neovim(self):
        super()._post_start_neovim()
        if self.external_server:
            self.vim.vars.set_p('tmux_socket', self.socket)
            id = self.session.windows[0].panes[0].id_i | -1
            wid = self.session.windows[0].id_i | -1
            sid = self.session.id_i | -1
            self.vim.vars.set_p('tmux_force_vim_pane_id', id)
            self.vim.vars.set_p('tmux_force_vim_win_id', wid)
            self.vim.vars.set_p('tmux_force_vim_session_id', sid)
        else:
            self._create_window()

    def teardown(self):
        super().teardown()
        self._teardown_server()
        if not self.external_server:
            self._close_window()

    @property
    def _plugins(self):
        return super()._plugins.cons('myo.plugins.tmux')

    @property
    def _window_name(self):
        return 'myo-spec-vim'

    def _create_window(self):
        self._vim_window = self.session.new_window(
            window_name=self._window_name)
        self._vim_pane = self._vim_window.panes[0]
        self.vim.vars.set_p('tmux_force_vim_session_id', self.session.id_i |
                            -1)
        self.vim.vars.set_p('tmux_force_vim_win_id',
                            self._vim_window.id_i | -1)
        self.vim.vars.set_p('tmux_force_vim_pane_id', self._vim_pane.id_i | -1)

    def _close_window(self):
        self._vim_window.kill()

    @property
    def _window(self):
        return (
            super()._window if self.external_server else
            self.session.windows.find(_.name == self._window_name)
            .get_or_fail('no window')
        )

    def _pane_count(self, count: int):
        return later(lambda: self._panes.should.have.length_of(count))

    def _size(self, attr, id, h):
        later(lambda: (self._pane_with_id(id) / attr).should.contain(h))

    def _height(self, id, h):
        return self._size(_.height, id, h)

    def _width(self, id, h):
        return self._size(_.width, id, h)


class ExternalTmuxIntegrationSpec(TmuxIntegrationSpecBase,
                                  MyoIntegrationSpec):

    @property
    def _tmux(self):
        return self.root.sub.find(_.title == 'tmux')

    @property
    def tmux(self):
        return (self.root.sub.find(_.title == 'tmux')
                .get_or_fail('no tmux plugin'))

    @property
    def _state(self):
        return Maybe(self.root.data.sub_state('tmux', None))

    @property
    def state(self):
        return self._state.get_or_fail('no tmux state yet')

    def wait_for_tmux(self):
        self._wait_for(lambda: self._tmux.present)

    def wait_for_state(self):
        self._wait_for(lambda: self._state.present)

    def _create_layout(self, name, **options):
        self.root.send_sync(TmuxCreateLayout(name, options=Map(options)))

    def _create_pane(self, name, **options):
        self.root.send_sync(TmuxCreatePane(name, options=Map(options)))

    def _open_pane(self, name, **options):
        self.root.send_sync(TmuxOpen(name, options=Map(options)))


class TmuxIntegrationSpec(TmuxIntegrationSpecBase, MyoPluginIntegrationSpec):

    def _create_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxCreatePane {}'.format(name), **kw)
        self._wait(.1)

    def _open_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxOpen {}'.format(name), **kw)
        self._wait(.1)

    def _close_pane(self, name):
        self.vim.cmd_sync('MyoTmuxClosePane {}'.format(name))
        self._wait(.1)


class DefaultLayoutSpec(TmuxIntegrationSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', True)


class TmuxCmdConf(CmdSpecConf):

    def _set_vars(self):
        super()._set_vars()
        self.vim.vars.set_p('tmux_use_defaults', True)
        self.vim.vars.set_p('tmux_vim_width', 10)
        self.vim.vars.set_p('tmux_watcher_interval', 0.1)

    def _py_shell(self):
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py',
                      langs=['python'])

    def _cmd_pid(self, id):
        return self._panes.find(__.id_i.contains(id)) // _.command_pid | 0


class TmuxCmdSpec(TmuxCmdConf, TmuxIntegrationSpec):
    pass


class XTmuxCmdSpec(TmuxCmdConf, ExternalTmuxIntegrationSpec):
    pass

__all__ = ('TmuxIntegrationSpec', 'DefaultLayoutSpec', 'TmuxCmdSpec',
           'XTmuxCmdSpec')
