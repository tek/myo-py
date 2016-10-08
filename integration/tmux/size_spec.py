from amino import List, __, _
from amino.test import later

from integration._support.tmux import TmuxIntegrationSpec, DefaultLayoutSpec


class OpenPaneSizeSpec(TmuxIntegrationSpec):

    def _pre_start(self):
        self.vim.vars.set_p('tmux_vim_width', 20)
        super()._pre_start()

    def open_pane_size(self):
        self._create_pane('pan1', parent='root', fixed_size=20)
        self._open_pane('pan1')
        self._width(1, 20)


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
        ''' Simple distribute with min/max sizes.
        Sizes and weights are chosen exactly.
        '''
        h1 = 8
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', min_size=5, max_size=h1,
                          weight=1)
        self._create_pane('pan2', parent='test', min_size=10, max_size=40,
                          weight=h1 + 1)
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._height(1, h1 - 1)

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

    def close(self):
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', weight=1)
        self._create_pane('pan2', parent='test', weight=1)
        self._create_pane('pan3', parent='test', weight=1)
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._open_pane('pan3')
        self._height(3, 13)
        self.vim.cmd_sync('MyoTmuxClosePane pan2')
        self._pane_count(3)
        self._height(3, 20)


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

    def minimize(self):
        mini = 5
        self._create_pane('pan', parent='root', fixed_size=20,
                          minimized_size=mini, weight=0)
        self._open_pane('pan')
        self.vim.cmd_sync('MyoTmuxMinimize pan')
        self._width(1, mini)

    def minimize_layout(self):
        mini = 5
        self.json_cmd_sync('MyoTmuxCreateLayout lay', parent='root',
                           fixed_size=20, minimized_size=mini, weight=0)
        self._create_pane('pan', parent='lay')
        self._open_pane('lay')
        self.vim.cmd_sync('MyoTmuxMinimize lay')
        self._width(1, mini)


class MinimizeSpec(TmuxIntegrationSpec):

    def _check(self, size):
        later(lambda: self._panes.find(__.id_i.contains(1))
              .map(_.height)
              .should.contain(size))

    def minimize(self):
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', minimized_size=5, fixed_size=10,
                          parent='test')
        self._create_pane('pan2', fixed_size=10, parent='test')
        self._create_pane('pan3', parent='test')
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._open_pane('pan3')
        self._pane_count(4)
        self._check(10)
        self.json_cmd_sync('MyoTmuxMinimize pan1')
        self._check(5)
        self.json_cmd_sync('MyoTmuxRestore pan1')
        self._check(10)

    def minimize_default(self):
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test')
        self._create_pane('pan2', parent='test')
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._pane_count(3)
        self.json_cmd_sync('MyoTmuxMinimize pan1')
        self._check(2)

    def open_or_toggle_pane(self):
        fix = 10
        mini = 5
        cmd = lambda: self.json_cmd_sync('MyoTmuxOpenOrToggle pan')
        self.json_cmd_sync('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane('pan', fixed_size=fix, minimized_size=mini,
                          parent='lay')
        self._create_pane('pan2', parent='lay', weight=1)
        cmd()
        self._wait(.1)
        self._open_pane('pan2')
        self._pane_count(3)
        self._height(1, fix)
        cmd()
        self._height(1, mini)
        cmd()
        self._height(1, fix)

    def open_or_toggle_layout(self):
        fix = 10
        mini = 5
        cmd = lambda: self.json_cmd_sync('MyoTmuxOpenOrToggle lay2')
        self.json_cmd_sync('MyoTmuxCreateLayout lay', parent='root')
        self.json_cmd_sync('MyoTmuxCreateLayout lay2', parent='lay',
                           fixed_size=fix, minimized_size=mini, weight=0)
        self._create_pane('pan', parent='lay2')
        self._create_pane('pan2', parent='lay', weight=1)
        cmd()
        self._wait(.1)
        self._open_pane('pan2')
        self._pane_count(3)
        self._wait(2)
        self._height(1, fix)
        cmd()
        self._height(1, mini)
        cmd()
        self._height(1, fix)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec',
           'DefaultLayoutDistributeSizeSpec')
