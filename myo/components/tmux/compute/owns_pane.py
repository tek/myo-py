from ribosome.compute.api import prog

from myo.ui.data.view import View


@prog.strict
def tmux_owns_view(view: View) -> bool:
    return view.ui == 'tmux'


__all__ = ('tmux_owns_view',)
