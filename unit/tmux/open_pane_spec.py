from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.io.compute import TmuxIO
from chiasma.data.session import Session
from chiasma.data.window import Window as TWindow

from amino import List, Map, __
from amino.boolean import true

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config
from ribosome.test.integration.klk import later

from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.ui.data.view import Layout, Pane
from myo.ui.data.space import Space
from myo.ui.data.window import Window
from myo.env import Env
from myo.config.component import MyoComponent


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
        window = Window.cons('win', layout=layout)
        space = Space.cons('spc', List(window))
        helper = (
            DispatchHelper.cons(config, 'ui', 'tmux', vars=dict(myo_tmux_socket=self.socket))
            .mod.state(
                __
                .modify_component_data('ui', __.append1.spaces(space))
                .modify_component_data(
                    'tmux',
                    __
                    .append1.sessions(Session.cons(space.ident, id=0))
                    .append1.windows(TWindow.cons(window.ident, id=0))
                )
            )
        )
        state = helper.loop('command:open_pane', args=('one', '{}')).unsafe(helper.vim)
        helper2 = helper.set.state(state)
        helper2.loop('command:open_pane', args=('two', '{}')).unsafe(helper.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(2)))


__all__ = ('OpenPaneSpec',)
