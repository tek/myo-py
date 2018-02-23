from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.io.compute import TmuxIO

from amino import List, Map
from amino.boolean import true

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config
from ribosome.test.integration.klk import later

from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.ui.data.view import Layout, Pane
from myo.env import Env
from myo.config.component import MyoComponent

from unit._support.tmux import init_tmux_data


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(ui=ui, tmux=tmux),
    component_config_type=MyoComponent,
)


class OpenPaneSpec(TmuxSpec):
    '''
    open a tmux pane $open_pane
    '''

    def open_pane(self) -> Expectation:
        layout = ViewTree.layout(
            Layout.cons('root', vertical=true),
            List(
                ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(max_size=10))),
                ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons(max_size=10))),
            )
        )
        helper = DispatchHelper.cons(config, 'ui', 'tmux', vars=dict(myo_tmux_socket=self.socket))
        window, space, helper1 = init_tmux_data(helper, layout)
        state = helper1.loop('command:open_pane', args=('one', '{}')).unsafe(helper.vim)
        helper2 = helper1.set.state(state)
        helper2.loop('command:open_pane', args=('two', '{}')).unsafe(helper.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(2)))


__all__ = ('OpenPaneSpec',)
