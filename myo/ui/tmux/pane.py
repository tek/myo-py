import tmuxp

from myo.ui.tmux.view import View

from trypnv.record import maybe_field, dfield, field


class Pane(View):
    id = maybe_field(str)
    name = field(str)
    open = dfield(False)

    @property
    def pane(self):
        return tmuxp.Pane

__all__ = ('Pane',)
