from kallikrein import Expectation, k

from chiasma.test.tmux_spec import TmuxSpec, tmux_spec_socket
from chiasma.commands.pane import all_panes, send_keys
from chiasma.util.id import StrIdent
from chiasma.data.tmux import TmuxData
from chiasma.data.session import Session
from chiasma.data.window import Window
from chiasma.data.pane import Pane

from amino import do, Do, Map, List, Just

from ribosome.test.integration.run import RequestHelper
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.api import N

from myo.components.tmux.compute.create_vim_pane import create_vim_pane, child_pids
from myo import myo_config
from myo.tmux.io import tmux_to_nvim


class CreateVimPaneSpec(TmuxSpec):
    '''
    discover the vim pane $discover
    '''

    def discover(self) -> Expectation:
        ident = StrIdent('p')
        helper = RequestHelper.strict(myo_config, 'tmux', vars=Map(myo_tmux_socket=tmux_spec_socket))
        @do(NvimIO[None])
        def run() -> Do:
            yield tmux_to_nvim(send_keys(0, List('tail')))
            ps = yield tmux_to_nvim(all_panes())
            pane = yield N.from_maybe(ps.head, 'no panes')
            pids = yield N.from_io(child_pids(pane.pid))
            pid = yield N.from_maybe(pids.head, 'no pids')
            yield create_vim_pane.code.code(ident, pid).run(helper.component_res_for('tmux'))
        (res, a) = run().unsafe(helper.vim)
        return k(res.data.comp) == TmuxData.cons(
            List(Session.cons(ident, 0)),
            List(Window.cons(ident, 0)),
            List(Pane.cons(ident, 0)),
            ident,
        )


__all__ = ('CreateVimPaneSpec',)
