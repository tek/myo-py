from chiasma.test.tmux_spec import TmuxSpec as ChiasmaTmuxSpec

from integration._support.base import DefaultSpec


class TmuxSpec(ChiasmaTmuxSpec, DefaultSpec):

    def __init__(self) -> None:
        ChiasmaTmuxSpec.__init__(self)
        DefaultSpec.__init__(self)

    def setup(self) -> None:
        ChiasmaTmuxSpec.setup(self)
        DefaultSpec.setup(self)


__all__ = ('TmuxSpec',)
