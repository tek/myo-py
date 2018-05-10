from kallikrein import Expectation, k

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import all_panes, send_keys
from chiasma.util.id import StrIdent
from chiasma.data.tmux import TmuxData
from chiasma.data.session import Session
from chiasma.data.window import Window
from chiasma.data.pane import Pane
from chiasma.util.pid import child_pids

from amino import do, Do, List

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N
from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test
from ribosome.compute.run import run_prog

from myo.components.tmux.compute.create_vim_pane import create_vim_pane
from myo.tmux.io import tmux_to_nvim
from myo.config.plugin_state import MyoState

from unit._support.tmux import tmux_default_test_config


@do(NS[MyoState, Expectation])
def discover_spec() -> Do:
    ident = StrIdent('p')
    @do(NvimIO[None])
    def run() -> Do:
        yield tmux_to_nvim(send_keys(0, List('tail')))
        ps = yield tmux_to_nvim(all_panes())
        pane = yield N.from_maybe(ps.head, 'no panes')
        pids = yield N.from_io(child_pids(pane.pid))
        yield N.from_maybe(pids.head, 'no pids')
    pid = yield NS.lift(run())
    yield run_prog(create_vim_pane, List(ident, pid))
    state = yield NS.inspect(lambda s: s.data_by_type(TmuxData))
    return k(state) == TmuxData.cons(
        List(Session.cons(ident, 0)),
        List(Window.cons(ident, 0)),
        List(Pane.cons(ident, 0)),
        ident,
    )


class CreateVimPaneSpec(TmuxSpec):
    '''
    discover the vim pane $discover
    '''

    def discover(self) -> Expectation:
        return unit_test(tmux_default_test_config(), discover_spec)


__all__ = ('CreateVimPaneSpec',)
