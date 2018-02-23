from typing import TypeVar

from amino.tc.base import tc_prop

from chiasma.io.compute import TmuxIO
from chiasma.tmux import Tmux
from chiasma.io.state import TmuxIOState

from ribosome.nvim.io import ToNvimIOState, NS
from ribosome.nvim import NvimIO, NvimFacade

A = TypeVar('A')
S = TypeVar('S')


def tmux_from_vim(vim: NvimFacade) -> Tmux:
    socket = vim.vars.p('tmux_socket') | None
    return Tmux.cons(socket=socket)


class TmuxStateToNvimIOState(ToNvimIOState, tpe=TmuxIOState):

    @tc_prop
    def nvim(self, fa: TmuxIOState[S, A]) -> NS:
        def tmux_to_nvim(tm: TmuxIO[A]) -> NvimIO[A]:
            return NvimIO.suspend(lambda v: NvimIO.from_either(tm.either(tmux_from_vim(v))))
        return fa.transform_f(NS, tmux_to_nvim)


__all__ = ('TmuxStateToNvimIOState',)
