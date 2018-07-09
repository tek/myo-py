import os

from kallikrein import Expectation, k
from kallikrein.matchers.length import have_length
from kallikrein.matchers import equal, contain

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import parse_pane_id, parse_bool, all_panes, close_pane_id
from chiasma.command import tmux_data_cmd, TmuxCmdData, simple_tmux_cmd_attr
from chiasma.data.view_tree import ViewTree
from chiasma.data.pane import Pane as TPane
from chiasma.io.state import TS

from test.klk.tmux import tmux_await_k, pane_count

from amino import do, Do, Dat, Either, List, IO
from amino.test.path import pkg_dir
from amino.test import temp_dir
from amino.lenses.lens import lens

from ribosome.test.unit import unit_test
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request

from myo.config.plugin_state import MyoState
from myo.ui.data.view import Layout, Pane

from test.tmux import two_panes, tmux_default_test_config, init_tmux_data, update_views


class PaneFocusData(Dat['PaneFocusData']):

    @staticmethod
    @do(Either[str, 'PaneFocusData'])
    def cons(
            pane_id: int,
            pane_active: bool,
    ) -> Do:
        id = yield parse_pane_id(pane_id)
        active = yield parse_bool(pane_active)
        return PaneFocusData(
            id,
            active,
        )

    def __init__(self, id: int, active: bool) -> None:
        self.id = id
        self.active = active


cmd_data_fdata = TmuxCmdData.from_cons(PaneFocusData.cons)


@do(TmuxIO[bool])
def pane_zero_focus() -> Do:
    data = yield tmux_data_cmd('list-panes', List('-a'), cmd_data_fdata)
    pane0 = yield TmuxIO.from_maybe(data.find(lambda a: a.id == 0), 'no pane 0')
    return pane0.active


def pane_cwds() -> TmuxIO[List[str]]:
    return simple_tmux_cmd_attr('list-panes', List('-a'), 'pane_current_path')


@do(NS[MyoState, Expectation])
def open_pane_spec() -> Do:
    path = pkg_dir()
    path = temp_dir('open_pane', 'cwd')
    yield two_panes()
    yield NS.from_io(IO.delay(os.chdir, str(path)))
    yield request('open_pane', 'one', '{}')
    yield request('open_pane', 'two', '{}')
    count = yield NS.lift(pane_count(2))
    cwd = yield NS.lift(tmux_await_k(contain(str(path)), pane_cwds))
    return count & cwd


@do(NS[MyoState, Expectation])
def focus_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield NS.lift(tmux_await_k(equal(True), pane_zero_focus))


pin_layout = ViewTree.layout(
    Layout.cons('root', vertical=False),
    List(
        ViewTree.pane(Pane.cons('one', open=True)),
        ViewTree.layout(
            Layout.cons('right', vertical=True),
            List(
                ViewTree.pane(Pane.cons('two', pin=True)),
                ViewTree.pane(Pane.cons('three')),
            )
        )
    )
)


@do(NS[MyoState, Expectation])
def pinned_sibling_spec() -> Do:
    yield init_tmux_data(pin_layout)
    yield update_views(lens.panes.set(List(TPane.cons('one', id=0))))
    yield request('open_pane', 'three')
    yield NS.lift(pane_count(3))


@do(NS[MyoState, Expectation])
def pinned_spec() -> Do:
    yield init_tmux_data(pin_layout)
    yield update_views(lens.panes.set(List(TPane.cons('one', id=0))))
    yield request('open_pane', 'two')
    yield NS.lift(pane_count(2))


@do(NS[MyoState, Expectation])
def manually_closed_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield request('open_pane', 'two', '{}')
    count1 = yield NS.lift(pane_count(2))
    yield TS.lift(close_pane_id(1)).nvim
    count2 = yield NS.lift(pane_count(1))
    yield request('open_pane', 'two', '{}')
    count3 = yield NS.lift(pane_count(2))
    return count1 & count2 & count3


class OpenPaneSpec(TmuxSpec):
    '''
    open a tmux pane $open_pane
    keep focus on vim $focus
    open pinned pane when opening sibling $pinned_sibling
    open pinned pane without opening others $pinned
    reopen manually closed pane $manually_closed
    '''

    def open_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), open_pane_spec)

    def focus(self) -> Expectation:
        return unit_test(tmux_default_test_config(), focus_spec)

    def pinned_sibling(self) -> Expectation:
        return unit_test(tmux_default_test_config(), pinned_sibling_spec)

    def pinned(self) -> Expectation:
        return unit_test(tmux_default_test_config(), pinned_spec)

    def manually_closed(self) -> Expectation:
        return unit_test(tmux_default_test_config(), manually_closed_spec)


__all__ = ('OpenPaneSpec',)
