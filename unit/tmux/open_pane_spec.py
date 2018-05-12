from kallikrein import Expectation
from kallikrein.matchers.length import have_length
from kallikrein.matchers import equal

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import parse_pane_id, parse_bool, all_panes
from chiasma.command import tmux_data_cmd, TmuxCmdData

from test.klk.tmux import tmux_await_k

from amino import do, Do, Dat, Either, List

from ribosome.test.unit import unit_test
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request

from myo.config.plugin_state import MyoState

from unit._support.tmux import two_panes, tmux_default_test_config


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


@do(NS[MyoState, Expectation])
def open_pane_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield request('open_pane', 'two', '{}')
    yield NS.lift(tmux_await_k(have_length(2), all_panes))


@do(NS[MyoState, Expectation])
def focus_spec() -> Do:
    yield two_panes()
    yield request('open_pane', 'one', '{}')
    yield NS.lift(tmux_await_k(equal(True), pane_zero_focus))


class OpenPaneSpec(TmuxSpec):
    '''
    open a tmux pane $open_pane
    keep focus on vim $focus
    '''

    def open_pane(self) -> Expectation:
        return unit_test(tmux_default_test_config(), open_pane_spec)

    def focus(self) -> Expectation:
        return unit_test(tmux_default_test_config(), focus_spec)


__all__ = ('OpenPaneSpec',)
