from amino import Boolean

from ribosome.compute.api import prog

from myo.ui.data.view import Pane


@prog.strict
def tmux_owns_pane(pane: Pane) -> Boolean:
    return pane.ui == 'tmux'


__all__ = ('tmux_owns_pane',)
