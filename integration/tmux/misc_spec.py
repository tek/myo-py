from integration._support.tmux import DefaultLayoutSpec, TmuxIntegrationSpec
from integration._support.command import CmdSpec

from amino.test import later
from amino import _


class ClosePaneSpec(DefaultLayoutSpec):

    def _check(self, length: int):
        return later(lambda: self._panes.should.have.length_of(length))

    def close(self):
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._check(1)
        self.vim.cmd('MyoTmuxClosePane make')
        self._wait(0.1)
        self._check(1)
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.cmd('MyoTmuxClosePane make')
        self._check(1)

    def auto_close(self):
        self.json_cmd('MyoTmuxOpenPane make')
        self._check(2)
        self.vim.doautocmd('VimLeave')
        self._check(1)


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
        self.json_cmd('MyoTmuxCreatePane pan1', parent='test', pin=True)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test')
        self.json_cmd('MyoTmuxOpenPane pan2')
        later(check)

_test_line = 'this is a test'


def _test_ctor():
    return 'echo \'{}\''.format(_test_line)


class RunTestSpec(DefaultLayoutSpec, CmdSpec):

    def target(self):
        self.vim.buffer.set_pvar('test_target', 'test')
        self.json_cmd_sync('MyoTmuxCreatePane test', parent='main')
        self.json_cmd_sync('MyoTest',
                           ctor='py:integration.tmux.misc_spec._test_ctor')
        later(lambda: self._panes.should.have.length_of(3))


class FocusSpec(TmuxIntegrationSpec):

    def no_focus(self):
        def check():
            (self._panes.head / _.active).should.contain(True)
        self.json_cmd('MyoTmuxCreatePane pan1')
        self.json_cmd_sync('MyoTmuxOpenPane pan1')
        later(lambda: self._panes.should.have.length_of(2))
        self._wait(.5)
        later(check)

    def focus(self):
        def check():
            (self._panes.lift(1) / _.active).should.contain(True)
        self.json_cmd('MyoTmuxCreatePane pan1', focus=True)
        self.json_cmd('MyoTmuxOpenPane pan1')
        later(check)

__all__ = ('ClosePaneSpec', 'ShowSpec')
