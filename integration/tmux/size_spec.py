from amino import List, __, _
from ribosome.test.integration.klk import later

from kallikrein import kf, Expectation
from kallikrein.matchers import contain
from kallikrein.matchers.comparison import less_equal

from integration._support.tmux import TmuxIntegrationSpec, DefaultLayoutSpec


class OpenPaneSizeSpec(TmuxIntegrationSpec):
    ''' size of an opened pane $open_pane_size
    '''

    def _pre_start(self) -> None:
        self.vim.vars.set_p('tmux_vim_width', 20)
        super()._pre_start()

    def open_pane_size(self) -> Expectation:
        self._create_pane('pan1', parent='root', fixed_size=20)
        self._open_pane('pan1')
        return self._width(1, 20)


class CutSizeSpec(TmuxIntegrationSpec):
    ''' cut sizes $cut_size
    '''

    def cut_size(self) -> Expectation:
        diff = lambda: (
            (self._panes.lift(1) & self._panes.lift(2))
            .map2(lambda a, b: abs(a.height - b.height)) |
            10)
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', min_size=100)
        self._create_pane('pan2', parent='test', min_size=100)
        self._open_pane('pan1')
        self._open_pane('pan2')
        return later(kf(diff).must(less_equal(1)))


class DistributeSizeSpec(TmuxIntegrationSpec):
    ''' distribute sizes
    simple distribute with min/max sizes
    sizes and weights are chosen exactly $basic
    default positions $default_positions
    move a pane $move
    close a pane $close
    '''

    def basic(self) -> Expectation:
        h1 = 8
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', min_size=5, max_size=h1,
                          weight=1)
        self._create_pane('pan2', parent='test', min_size=10, max_size=40,
                          weight=h1 + 1)
        self._open_pane('pan1')
        self._open_pane('pan2')
        return self._height(1, h1 - 1)

    def default_positions(self) -> Expectation:
        sz1, sz2 = 5, 10
        check = lambda: (
            self._panes
            .filter((_.id_i | 0) > 0)
            .sort_by(_.top)
            .map(_.height)
            .drop(1)
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
        return later(kf(check) == List(sz1, sz2))

    def move(self) -> Expectation:
        sz1, sz2 = 5, 10
        check = lambda: (
            self._panes
            .filter((_.id_i | 0) > 0)
            .sort_by(_.top)
            .map(_.height)[:2]
        )
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', position=1, weight=1)
        self._create_pane('pan2', parent='test', position=0.5, fixed_size=sz1)
        self._create_pane('pan3', parent='test', position=0.7, fixed_size=sz2)
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._open_pane('pan3')
        return later(kf(check) == List(sz1, sz2))

    def close(self) -> Expectation:
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
        return self._height(3, 20)


class DefaultLayoutDistributeSizeSpec(DefaultLayoutSpec):
    ''' size distribution in the default layout

    basic $basic
    minimize a pane $minimize
    minimize a layout $minimize_layout
    '''

    def _set_vars(self) -> None:
        super()._set_vars()
        self.vim_width = 10
        self.vim.vars.set_p('tmux_vim_width', self.vim_width)

    def basic(self) -> Expectation:
        target = List(self.vim_width, self.win_width - self.vim_width)
        self._open_pane('make')
        return later(kf(lambda: self._sizes / __[0]) == target)

    def minimize(self) -> Expectation:
        mini = 5
        self._create_pane('pan', parent='root', fixed_size=20,
                          minimized_size=mini, weight=0)
        self._open_pane('pan')
        self.vim.cmd_sync('MyoTmuxMinimize pan')
        return self._width(1, mini)

    def minimize_layout(self) -> Expectation:
        mini = 5
        self.json_cmd_sync('MyoTmuxCreateLayout lay', parent='root',
                           fixed_size=20, minimized_size=mini, weight=0)
        self._create_pane('pan', parent='lay')
        self._open_pane('lay')
        self.vim.cmd_sync('MyoTmuxMinimize lay')
        return self._width(1, mini)


class MinimizeSpec(TmuxIntegrationSpec):

    def _check(self, size: int) -> Expectation:
        return later(kf(lambda: self._pane_with_id(1).map(_.height))
                     .must(contain(size)))

    def minimize(self) -> Expectation:
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
        return self._check(10)

    def minimize_default(self) -> Expectation:
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test')
        self._create_pane('pan2', parent='test')
        self._open_pane('pan1')
        self._open_pane('pan2')
        self._pane_count(3)
        self.json_cmd_sync('MyoTmuxMinimize pan1')
        return self._check(2)

    def open_or_toggle_pane(self) -> Expectation:
        fix = 10
        mini = 5
        def cmd() -> None:
            return self.json_cmd_sync('MyoTmuxOpenOrToggle pan')
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
        return self._height(1, fix)

    def open_or_toggle_layout(self) -> Expectation:
        fix = 10
        mini = 5
        def cmd() -> None:
            return self.json_cmd_sync('MyoTmuxOpenOrToggle inner')
        self._create_layout('outer')
        self._create_layout('inner', 'outer', fixed_size=fix,
                            minimized_size=mini, weight=0)
        self._create_pane('in_inner', parent='inner')
        self._create_pane('in_outer', parent='outer', weight=1, position=1)
        cmd()
        self._open_pane('in_outer')
        self._pane_count(3)
        self._height(1, fix)
        cmd()
        self._height(1, mini)
        cmd()
        return self._height(1, fix)

__all__ = ('CutSizeSpec', 'DistributeSizeSpec', 'DefaultLayoutDistributeSizeSpec')
