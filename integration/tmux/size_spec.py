from amino import List, __, _
from amino.test import later

from integration._support.tmux import TmuxIntegrationSpec, DefaultLayoutSpec


class CutSizeSpec(TmuxIntegrationSpec):

    def cut_size(self):
        def check():
            diff = (
                (self._panes.lift(1) & self._panes.lift(2))
                .map2(lambda a, b: abs(a.height - b.height)) |
                10)
            (diff <= 1).should.be.ok
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', min_size=100)
        self._create_pane('pan2', parent='test', min_size=100)
        self._open_pane('pan1')
        self._open_pane('pan2')
        later(check)


class DistributeSizeSpec(TmuxIntegrationSpec):

    def distribute(self):
        h1 = 8
        check = lambda: (self._sizes / __[1]).last.should.contain(h1)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', min_size=5, max_size=h1,
                          weight=1)
        self._create_pane('pan2', parent='test', min_size=10, max_size=40,
                          weight=h1 + 1)
        self._open_pane('pan1')
        self._wait(.1)
        self._open_pane('pan2')
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
        self._create_pane('pan1', parent='test', weight=1)
        self._wait(.1)
        self._create_pane('pan2', parent='test', fixed_size=sz1)
        self._wait(.1)
        self._create_pane('pan3', parent='test', fixed_size=sz2)
        self._open_pane('pan1')
        self._wait(.1)
        self._open_pane('pan2')
        self._wait(.1)
        self._open_pane('pan3')
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
        self.vim.vars.set_p('tmux_vim_width', self.vim_width)

    def distribute(self):
        def check():
            widths = self._sizes / __[0]
            target = List(self.vim_width, self.win_width - self.vim_width)
            widths.should.equal(target)
        self._open_pane('make')
        later(check)


class MinimizeSpec(TmuxIntegrationSpec):

    def minimize(self):
        def check(size):
            later(lambda: self._panes.find(__.id_i.contains(1))
                  .map(_.height)
                  .should.contain(size))
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', minimized_size=5, fixed_size=10,
                          parent='test')
        self._create_pane('pan2', fixed_size=10, parent='test')
        self._create_pane('pan3', parent='test')
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._open_pane('pan3')
        self._pane_count(4)
        check(10)
        self.json_cmd_sync('MyoTmuxMinimize pan1')
        check(5)
        self.json_cmd_sync('MyoTmuxRestore pan1')
        check(10)

    def open_or_toggle(self):
        fix = 10
        mini = 5
        cmd = lambda: self.json_cmd_sync('MyoTmuxOpenOrToggle pan')
        def height(h):
            later(lambda: (self._pane_with_id(2) / _.height).should.contain(h))
        self.json_cmd_sync('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan', fixed_size=fix, minimized_size=mini,
                          parent='test')
        self._create_pane('pan2', parent='test', weight=1)
        self._open_pane('pan2')
        cmd()
        self._pane_count(3)
        height(fix)
        cmd()
        height(mini)
        cmd()
        height(fix)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec',
           'DefaultLayoutDistributeSizeSpec')
