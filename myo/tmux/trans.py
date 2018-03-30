from typing import TypeVar

from ribosome.dispatch.transform import TransformTransState
from ribosome.dispatch.data import DispatchOutput

from chiasma.io.state import TmuxIOState
from chiasma.io.compute import TmuxIO

import myo.tmux.io  # noqa

D = TypeVar('D')


class TransformTmuxIOState(TransformTransState[TmuxIO], tpe=TmuxIOState):

    def run(self, st: TmuxIOState[D, DispatchOutput]) -> TmuxIOState[D, DispatchOutput]:
        return st.nvim


__all__ = ('TransformTmuxIOState',)
