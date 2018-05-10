from typing import Callable, Any, TypeVar

from kallikrein import Expectation, k
from kallikrein.matcher import Matcher

from chiasma.io.compute import TmuxIO

from amino import do, Do

from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk.expectation import await_k

from myo.tmux.io import tmux_to_nvim

A = TypeVar('A')


def tmux_await_k(
        matcher: Matcher[A],
        io: Callable[..., TmuxIO[A]],
        *a: Any,
        timeout: int=1,
        interval: float=.25,
        **kw: Any,
) -> NvimIO[Expectation]:
    @do(NvimIO[bool])
    def check() -> Do:
        result = yield tmux_to_nvim(io(*a, **kw))
        return k(result).must(matcher)
    return await_k(check)


__all__ = ('tmux_await_k',)
