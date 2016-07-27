from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane
from myo.ui.tmux.layout_handler import LayoutHandler

from unit._support.spec import TmuxUnitSpec


class Tmux_(TmuxUnitSpec):

    def mk_server(self):
        from datetime import datetime
        pane = Pane(name='pan')
        layout = Layout(panes=[pane], name='lay')
        tmux = LayoutHandler(self.server)
        self.session.windows[0].panes
        import time
        time.sleep(1)

__all__ = ('Tmux_',)
