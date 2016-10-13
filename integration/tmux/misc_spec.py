from amino.test import later
from amino import _

from myo.ui.tmux.facade.window import pane_not_found_error
from myo.plugins.tmux.main import invalid_pane_name

from integration._support.tmux import (DefaultLayoutSpec, TmuxIntegrationSpec,
                                       ExternalTmuxIntegrationSpec)


class CreateLayoutSpec(ExternalTmuxIntegrationSpec):

    def create(self):
        self.plugin.myo_start()
        name = 'lay'
        self._create_layout(name, parent='root')
        l = self.state.sessions.head // _.windows.head // _.root.layouts.last
        (l / _.name).should.contain(name)


class CreatePaneSpec(ExternalTmuxIntegrationSpec):

    def create(self):
        self.plugin.myo_start()
        lname = 'lay'
        pname = 'pan'
        self._create_layout(lname, parent='root')
        self._create_pane(pname, parent=lname)
        p = (self.state.sessions.head // _.windows.head //
             _.root.layouts.last // _.panes.head)
        (p / _.name).should.contain(pname)


class XOpenSpec(ExternalTmuxIntegrationSpec):

    def create(self):
        self.vim.vars.set_p('tmux_no_watcher', True)
        self.plugin.myo_start()
        lname = 'lay'
        pname = 'pan'
        self._create_layout(lname, parent='root')
        self._create_pane(pname, parent=lname)
        self._open_pane(pname)
        self._pane_count(2)


class OpenPaneSpec(TmuxIntegrationSpec):

    def open(self):
        pan = 'pan'
        self.json_cmd('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane(pan, parent='lay')
        self._open_pane(pan)
        self._pane_count(2)
        pan1 = 'pan1'
        self._open_pane(pan1)
        self._log_contains(invalid_pane_name.format(pan1))


class ClosePaneSpec(DefaultLayoutSpec):

    def close(self):
        pane = 'make'
        self._open_pane(pane)
        self._pane_count(2)
        self._close_pane(pane)
        self._pane_count(1)
        self._close_pane(pane)
        self._pane_count(1)
        self._log_contains(pane_not_found_error.format(pane))
        self._open_pane(pane)
        self._pane_count(2)
        self._close_pane(pane)
        self._pane_count(1)

    def auto_close(self):
        self._open_pane('make')
        self._pane_count(2)
        self.vim.doautocmd('VimLeave')
        self._pane_count(1)


class ShowSpec(TmuxIntegrationSpec):

    def output(self):
        def check():
            self._log_out.should_not.be.empty
        self.vim.cmd('MyoTmuxShow')
        later(check)


class PinSpec(TmuxIntegrationSpec):

    def open(self):
        check = lambda: self._panes.length.should.equal(3)
        def check2():
            (self._panes.find(_.height == 2) / _.active).should.contain(True)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', pin=True)
        self._create_pane('pan2', parent='test', focus=True, fixed_size=2)
        self._open_pane('pan2')
        later(check)
        later(check2)


class FocusSpec(TmuxIntegrationSpec):

    def open_no_focus(self):
        check = lambda i: (self._panes.lift(i) / _.active).should.contain(True)
        self._create_pane('pan1')
        self._open_pane('pan1')
        self._pane_count(2)
        later(check, 0)
        self.vim.cmd_sync('MyoTmuxFocus pan1')
        later(check, 1)

    def open_focus(self):
        check = lambda: (self._panes.lift(1) / _.active).should.contain(True)
        self._create_pane('pan1', focus=True)
        self._open_pane('pan1')
        later(check)


class OpenLayoutSpec(TmuxIntegrationSpec):

    def _pre_start(self):
        super()._pre_start()
        self.json_cmd('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane('pan1', parent='lay')

    def open(self):
        self._open_pane('lay')
        self._pane_count(2)

    def toggle(self):
        self.json_cmd('MyoTmuxOpenOrToggle lay')
        self._pane_count(2)

    def minimize(self):
        self.json_cmd('MyoTmuxCreateLayout lay2', parent='root')
        self._create_pane('pan2', parent='lay2')
        self._open_pane('lay')
        self._open_pane('lay2')
        self._pane_count(3)
        self.json_cmd('MyoTmuxMinimize lay2')
        later(lambda: (self._pane_with_id(2) / _.width).should.contain(2))

    def open_twice(self):
        self._create_pane('pan', parent='lay')
        self.vim.cmd_sync('MyoTmuxOpen lay')
        self._pane_count(2)
        self.vim.cmd_sync('MyoTmuxOpen lay')
        self._wait(1)
        self._pane_count(2)


class UpdateVimWindowSpec(ExternalTmuxIntegrationSpec):

    def window_size(self):
        self.plugin.myo_start()
        self.wait_for_state()
        sz = self._window.size
        later(lambda:
              (self.state.vim_window // _.size).should.contain(sz)
              )

__all__ = ('ClosePaneSpec', 'ShowSpec')
