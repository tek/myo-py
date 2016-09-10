from integration._support.tmux import DefaultLayoutSpec, TmuxIntegrationSpec

from amino.test import later
from amino import _


class ClosePaneSpec(DefaultLayoutSpec):

    def close(self):
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
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', pin=True)
        self._create_pane('pan2', parent='test')
        self._open_pane('pan2')
        later(check)


class FocusSpec(TmuxIntegrationSpec):

    def no_focus(self):
        def check():
            (self._panes.head / _.active).should.contain(True)
        self._create_pane('pan1')
        self._open_pane('pan1')
        self._pane_count(2)
        self._wait(.5)
        later(check)

    def focus(self):
        def check():
            (self._panes.lift(1) / _.active).should.contain(True)
        self._create_pane('pan1', focus=True)
        self._open_pane('pan1')
        later(check)

__all__ = ('ClosePaneSpec', 'ShowSpec')
