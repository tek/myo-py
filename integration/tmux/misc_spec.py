from ribosome.test.integration.klk import later
from amino import _

from kallikrein import Expectation, k, kf
from kallikrein.matchers import contain
from kallikrein.matchers.empty import be_nonempty

from myo.ui.tmux.facade.window import pane_not_found_error
from myo.plugins.tmux.main import invalid_pane_name

from integration._support.tmux import DefaultLayoutSpec, TmuxIntegrationSpec, ExternalTmuxIntegrationSpec


class CreateLayoutSpec(ExternalTmuxIntegrationSpec):
    '''create a layout $create
    '''

    def create(self) -> Expectation:
        name = 'lay'
        self._create_layout(name, parent='root')
        l = self.state.sessions.head // _.windows.head // _.root.layouts.last
        return k(l / _.name).must(contain(name))


class CreatePaneSpec(ExternalTmuxIntegrationSpec):
    '''create a pane $create
    '''

    def create(self) -> Expectation:
        lname = 'lay'
        pname = 'pan'
        self._create_layout(lname, parent='root')
        self._create_pane(pname, parent=lname)
        p = (self.state.sessions.head // _.windows.head //
             _.root.layouts.last // _.panes.head)
        return k(p / _.name).must(contain(pname))


class XOpenSpec(ExternalTmuxIntegrationSpec):
    '''open a pane (external spec) $open
    '''

    def _set_vars(self) -> None:
        super()._set_vars()
        self.vim.vars.set_p('tmux_no_watcher', True)

    def open(self) -> Expectation:
        lname = 'lay'
        pname = 'pan'
        self._create_layout(lname, parent='root')
        self._create_pane(pname, parent=lname)
        self._open_pane(pname)
        return self._pane_count(2)


class OpenPaneSpec(TmuxIntegrationSpec):
    '''open a pane $open
    '''

    def open(self) -> Expectation:
        pan = 'pan'
        self.json_cmd('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane(pan, parent='lay')
        self._open_pane(pan)
        self._pane_count(2)
        pan1 = 'pan1'
        self._open_pane(pan1)
        return self._log_contains(invalid_pane_name.format(pan1))


class ClosePaneSpec(DefaultLayoutSpec):
    '''close a pane $close
    autoclose a pane on `VimLeave` $auto_close
    '''

    def close(self) -> Expectation:
        pane = 'make'
        self._open_pane(pane)
        self._pane_count(2)
        self._close_pane(pane)
        self._pane_count(1)
        self._close_pane(pane)
        self._pane_count(1)
        self._log_contains(pane_not_found_error.format(pane))
        self._open_pane(pane)
        self._pane_count(2)
        self._close_pane(pane)
        return self._pane_count(1)

    def auto_close(self) -> Expectation:
        self._open_pane('make')
        self._pane_count(2)
        self.vim.doautocmd('VimLeave')
        return self._pane_count(1)


class ShowSpec(TmuxIntegrationSpec):
    '''display tmux information with `MyoTmuxShow` $output
    '''

    def output(self) -> Expectation:
        self.vim.cmd('MyoTmuxShow')
        return later(kf(lambda: self._log_out).must(be_nonempty))


class PinSpec(TmuxIntegrationSpec):
    '''automatically open a pinned pane when its parent is opened $open
    '''

    def open(self) -> Expectation:
        self.json_cmd('MyoTmuxCreateLayout test', parent='root')
        self._create_pane('pan1', parent='test', pin=True)
        self._create_pane('pan2', parent='test', focus=True, fixed_size=2)
        self._open_pane('pan2')
        later(kf(lambda: self._panes.length) == 3)
        return later(kf(lambda: self._panes.find(_.height == 2) / _.active).must(contain(True)))


class FocusSpec(TmuxIntegrationSpec):
    '''changing the focused pane
    opened pane aren't focused by default; switch focus manually $open_no_focus
    panes with `focus=True` are focused when opened $open_focus
    '''

    def open_no_focus(self) -> Expectation:
        def checker(i: int) -> Expectation:
            return kf(lambda: self._panes.lift(i) / _.active).must(contain(True))
        self._create_pane('pan1')
        self._open_pane('pan1')
        self._pane_count(2)
        later(checker(0))
        self.vim.cmd_sync('MyoTmuxFocus pan1')
        return later(checker(1))

    def open_focus(self) -> Expectation:
        self._create_pane('pan1', focus=True)
        self._open_pane('pan1')
        return later(kf(lambda: self._panes.lift(1) / _.active).must(contain(True)))


class OpenLayoutSpec(TmuxIntegrationSpec):
    '''opening layouts
    open the reference pane when opening a layout $open
    open the reference pane when toggling a closed layout $toggle
    minimize a layouts pane with `MyoTmuxMinimize` $minimize
    do nothing when opening a layout with already open panes $open_twice
    '''

    def _pre_start(self) -> None:
        super()._pre_start()
        self.json_cmd('MyoTmuxCreateLayout lay', parent='root')
        self._create_pane('pan1', parent='lay')

    def open(self) -> Expectation:
        self._open_pane('lay')
        return self._pane_count(2)

    def toggle(self) -> Expectation:
        self.json_cmd('MyoTmuxOpenOrToggle lay')
        return self._pane_count(2)

    def minimize(self) -> Expectation:
        self.json_cmd('MyoTmuxCreateLayout lay2', parent='root')
        self._create_pane('pan2', parent='lay2')
        self._open_pane('lay')
        self._open_pane('lay2')
        self._pane_count(3)
        self.json_cmd('MyoTmuxMinimize lay2')
        return later(kf(lambda: (self._pane_with_id(2) / _.width)).must(contain(2)))

    def open_twice(self) -> Expectation:
        self._create_pane('pan', parent='lay')
        self.vim.cmd_sync('MyoTmuxOpen lay')
        self._pane_count(2)
        self.vim.cmd_sync('MyoTmuxOpen lay')
        self._wait(1)
        return self._pane_count(2)


class UpdateVimWindowSpec(ExternalTmuxIntegrationSpec):
    '''the main window size is stored in the state $window_size
    '''

    def window_size(self) -> Expectation:
        self.wait_for_state()
        sz = self._window.size
        return later(kf(lambda: self.state.vim_window // _.size).must(contain(sz)))

__all__ = ('ClosePaneSpec', 'ShowSpec', 'CreateLayoutSpec', 'CreatePaneSpec', 'XOpenSpec', 'OpenPaneSpec', 'PinSpec',
           'FocusSpec', 'OpenLayoutSpec', 'UpdateVimWindowSpec')
