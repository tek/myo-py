from kallikrein import Expectation
from kallikrein.matchers import contain

from chiasma.test.tmux_spec import TmuxSpec

from amino import do, Do

from ribosome.dispatch.execute import eval_trans
from ribosome.plugin_state import RootDispatch
from ribosome.test.klk import kn
from ribosome.nvim.io.compute import NvimIO
from ribosome.dispatch.run import DispatchState

from myo.components.core.trans.info import collect_info

from unit._support.tmux import two_panes


class InfoSpec(TmuxSpec):
    '''
    show information about the state $info
    '''

    def tmux_in_terminal(self) -> bool:
        return False

    def info(self) -> Expectation:
        helper = two_panes()
        ds = DispatchState(helper.state, RootDispatch())
        @do(NvimIO[None])
        def run() -> Do:
            (s1, a) = yield eval_trans.match(collect_info()).run(ds)
            return 1
        return kn(helper.vim, run).must(contain(1))


__all__ = ('InfoSpec',)
