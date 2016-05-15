import tmuxp

from myo.ui.tmux.view import View

from tryp import _, __

from trypnv.record import dfield, maybe_field, list_field, field


class Layout(View):
    name = field(str)
    flex = dfield(False)
    min_size = dfield(0)
    max_size = maybe_field(int)
    panes = list_field()
    layouts = list_field()

    def find_pane(self, name):
        return (self.panes.find(_.name == name)
                .or_else(lambda: self._find_pane_in_layouts(name)))

    def _find_pane_in_layouts(self, name):
        return self.layouts.deep_find(__.find_pane(name))


class LayoutDirection():
    vertical = 0
    horizontal = 1


class LinearLayout(Layout):
    direction = dfield(LayoutDirection.vertical)


class LayoutHandler:

    def __init__(self, server: tmuxp.Server) -> None:
        self.server = server

    def create_pane(self, layout, pane):
        pass

__all__ = ('Layout',)
