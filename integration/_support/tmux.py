from integration._support.base import (MyoPluginIntegrationSpec,
                                       MyoIntegrationSpec)
from integration._support.command import CmdSpec

from amino.test import later
from amino import _, __, Map

from myo.test.spec import TmuxSpecBase
from myo.plugins.tmux.message import TmuxCreateLayout, TmuxCreatePane


class TmuxIntegrationSpecBase(TmuxSpecBase):

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
    def tmux(self):
        return (self.root.sub.find(_.title == 'tmux')
                .get_or_fail('no tmux plugin'))

    @property
    def state(self):
        def fail():
            raise Exception('no tmux state yet')
        return self.root.data.sub_state('tmux', lambda: fail)

    def _create_layout(self, name, **options):
        self.root.send_sync(TmuxCreateLayout(name, options=Map(options)))

    def _create_pane(self, name, **options):
        self.root.send_sync(TmuxCreatePane(name, options=Map(options)))


class TmuxIntegrationSpec(TmuxIntegrationSpecBase, MyoPluginIntegrationSpec):

    def _create_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxCreatePane {}'.format(name), **kw)
        self._wait(.1)

    def _open_pane(self, name, **kw):
        self.json_cmd_sync('MyoTmuxOpen {}'.format(name), **kw)
        self._wait(.1)


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

    def _py_shell(self):
        self._create_pane('py', parent='main')
        self.json_cmd('MyoShell py', line='python', target='py',
                      langs=['python'])

    def _cmd_pid(self, id):
        return self._panes.find(__.id_i.contains(id)) // _.command_pid | 0

__all__ = ('TmuxIntegrationSpec', 'DefaultLayoutSpec', 'TmuxCmdSpec')
