from integration._support.tmux import DefaultLayoutSpec, TmuxIntegrationSpec

from amino.test import later
from amino import _


class OpenSpec(TmuxIntegrationSpec):

    def open(self):
        self.json_cmd('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane('pan', parent='lay')
        self._open_pane('pan')
        self._pane_count(2)


class ClosePaneSpec(DefaultLayoutSpec):

    def _close(self):
        self._open_pane('make')
        self._pane_count(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._pane_count(1)
        self.vim.cmd('MyoTmuxClosePane make')
        self._wait(0.1)
        self._pane_count(1)
        self._open_pane('make')
        self._pane_count(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._pane_count(1)

    def _auto_close(self):
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

__all__ = ('ClosePaneSpec', 'ShowSpec')
