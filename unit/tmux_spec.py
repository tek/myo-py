from myo.ui.tmux.layout import Layout, LayoutHandler
from myo.ui.tmux.pane import Pane

from unit._support.spec import TmuxUnitSpec


class Tmux_(TmuxUnitSpec):

    def mk_server(self):
        pane = Pane()
        layout = Layout(panes=[pane])
        tmux = LayoutHandler()
        tmux.create_pane(layout, pane)
        print(self.session)
        print(self.session.windows)
        import time
        time.sleep(1)

__all__ = ('Tmux_',)
