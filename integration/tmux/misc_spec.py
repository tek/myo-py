from integration._support.tmux import DefaultLayoutSpec, TmuxIntegrationSpec

from amino.test import later


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
        self._wait(.1)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan2')
        self._wait(.1)
        later(check)

__all__ = ('ClosePaneSpec', 'ShowSpec')
