from tryp import List, _
from tryp.test import later

from integration._support.base import TmuxIntegrationSpec


class _TmuxSpec(TmuxIntegrationSpec):

    @property
    def _plugins(self):
        self._debug = True
        return List('myo.plugins.tmux')


class CutSizeSpec(_TmuxSpec):

    def open_pane(self):
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            panes.should.have.length_of(2)
        self.json_cmd('MyoTmuxCreatePane pan', parent='root', min_size=0.5,
                      weight=0.1)
        self.json_cmd('MyoTmuxOpenPane pan')
        later(check)


class DistributeSizeSpec(_TmuxSpec):

    def distribute_size(self):
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


class DefaultLayoutSpec(_TmuxSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim_width = 10
        self.vim.set_pvar('tmux_use_defaults', True)
        self.vim.set_pvar('tmux_vim_width', self.vim_width)

    def default_layout(self):
        def check():
            widths = self.sessions.head // _.windows // _.panes / _.size[0]
            target = List(self.vim_width, self.win_width - self.vim_width)
            widths.should.equal(target)
        self.json_cmd('MyoTmuxOpenPane make')
        later(check)


class DispatchSpec(_TmuxSpec):

    @property
    def _plugins(self):
        return super()._plugins.cat('myo.plugins.command')

    def _set_vars(self):
        super()._set_vars()
        self.vim.set_pvar('tmux_use_defaults', True)

    def run_cmd(self):
        def check():
            panes = self.sessions.head // _.windows.head / _.panes | List()
            out = panes // _.capture
            out.should.contain(s)
        s = 'cmd test'
        self.json_cmd('MyoShellCommand test', line="echo '{}'".format(s))
        self.json_cmd('MyoTmuxOpenPane make')
        self.json_cmd('MyoRun test', pane='make')
        later(check)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec', 'DefaultLayoutSpec',
           'DispatchSpec')
