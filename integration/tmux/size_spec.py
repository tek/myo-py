from amino import List, _
from amino.test import later

from integration._support.tmux import TmuxIntegrationSpec, DefaultLayoutSpec


class CutSizeSpec(TmuxIntegrationSpec):

    def cut_size(self):
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            panes.should.have.length_of(2)
        self.json_cmd('MyoTmuxCreatePane pan', parent='root', min_size=0.5,
                      weight=0.1)
        self.json_cmd('MyoTmuxOpenPane pan')
        later(check)


class DistributeSizeSpec(TmuxIntegrationSpec):

    def distribute(self):
        h1 = 7
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            sizes = panes[1:] / _.size / _[1]
            sizes.head.should.contain(h1)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self.json_cmd('MyoTmuxCreatePane pan1', parent='test', min_size=5,
                      max_size=h1, weight=1)
        self._wait(.1)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test', min_size=10,
                      max_size=40, weight=9)
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan1')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan2')
        later(check)


class DefaultLayoutDistributeSizeSpec(DefaultLayoutSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim_width = 10
        self.vim.set_pvar('tmux_vim_width', self.vim_width)

    def distribute(self):
        def check():
            widths = self.sessions.head // _.windows // _.panes / _.size[0]
            target = List(self.vim_width, self.win_width - self.vim_width)
            widths.should.equal(target)
        self.json_cmd('MyoTmuxOpenPane make')
        later(check)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec',
           'DefaultLayoutDistributeSizeSpec')
