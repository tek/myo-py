from amino import Boolean

from ribosome.trans.api import trans

from myo.ui.data.view import Pane


@trans.free.result()
def tmux_owns_pane(pane: Pane) -> Boolean:
    return pane.ui == 'tmux'


__all__ = ('tmux_owns_pane',)
