from amino import List, __, _
from amino.test import later

from integration._support.tmux import TmuxIntegrationSpec, DefaultLayoutSpec


# FIXME does nothing
class CutSizeSpec(TmuxIntegrationSpec):

    def cut_size(self):
        self.json_cmd('MyoTmuxCreatePane pan', parent='root', min_size=0.5,
                      weight=0.1)
        self.json_cmd('MyoTmuxOpenPane pan')
        self._pane_count(2)


class DistributeSizeSpec(TmuxIntegrationSpec):

    def distribute(self):
        h1 = 8
        check = lambda: (self._sizes / __[1]).last.should.contain(h1)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self.json_cmd('MyoTmuxCreatePane pan1', parent='test', min_size=5,
                      max_size=h1, weight=1)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test', min_size=10,
                      max_size=40, weight=9)
        self.json_cmd('MyoTmuxOpenPane pan1')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan2')
        later(check)

    def default_positions(self):
        sz1, sz2 = 5, 10
        check = lambda: (
            self._panes
            .filter((_.id_i | 0) > 0)
            .sort_by(_.top)
            .map(_.height)
            .drop(1)
            .should.equal(List(sz1, sz2))
        )
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self.json_cmd('MyoTmuxCreatePane pan1', parent='test', weight=1)
        self._wait(.1)
        self.json_cmd('MyoTmuxCreatePane pan2', parent='test', fixed_size=sz1)
        self._wait(.1)
        self.json_cmd('MyoTmuxCreatePane pan3', parent='test', fixed_size=sz2)
        self.json_cmd('MyoTmuxOpenPane pan1')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan2')
        self._wait(.1)
        self.json_cmd('MyoTmuxOpenPane pan3')
        later(check)

    def move(self):
        sz1, sz2 = 5, 10
        check = lambda: (
            self._panes
            .filter((_.id_i | 0) > 0)
            .sort_by(_.top)
            .map(_.height)[:2]
            .should.equal(List(sz1, sz2))
        )
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', position=1, weight=1)
        self._create_pane('pan2', parent='test', position=0.5, fixed_size=sz1)
        self._create_pane('pan3', parent='test', position=0.7, fixed_size=sz2)
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._open_pane('pan3')
        later(check)


class DefaultLayoutDistributeSizeSpec(DefaultLayoutSpec):

    def _set_vars(self):
        super()._set_vars()
        self.vim_width = 10
        self.vim.set_pvar('tmux_vim_width', self.vim_width)

    def distribute(self):
        def check():
            widths = self._sizes / __[0]
            target = List(self.vim_width, self.win_width - self.vim_width)
            widths.should.equal(target)
        self.json_cmd('MyoTmuxOpenPane make')
        later(check)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec',
           'DefaultLayoutDistributeSizeSpec')
