from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.io.compute import TmuxIO
from chiasma.data.pane import Pane as TPane

from amino import List, Map, __, _, L
from amino.boolean import true
from amino.lenses.lens import lens

from ribosome.config.config import Config
from ribosome.test.integration.klk import later

from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.ui.data.view import Layout, Pane
from myo.env import Env
from myo.config.component import MyoComponent
from myo.ui.pane import map_panes_in_spaces

from unit._support.tmux import init_tmux_data


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(ui=ui, tmux=tmux),
    component_config_type=MyoComponent,
)


class ClosePaneSpec(TmuxSpec):
    '''
    close a tmux pane $close_pane
    '''

    def close_pane(self) -> Expectation:
        layout = ViewTree.layout(
            Layout.cons('root', vertical=true),
            List(
                ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons(max_size=10))),
                ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons(max_size=10))),
            )
        )
        window, space, helper = init_tmux_data(layout)
        helper1 = helper.mod.state(
            __
            .modify_component_data(
                'tmux',
                __.set.panes(List(TPane.cons('one', id=0), TPane.cons('two', id=1)))
            )
            .modify_component_data(
                'ui',
                __.mod.spaces(L(map_panes_in_spaces)(lambda a: True, lens.open.set(true), _))
            )
        )
        TmuxIO.write('split-window').unsafe(self.tmux)
        self._wait(1)
        helper1.loop('command:close_pane', args=('one',)).unsafe(helper.vim)
        return later(kf(TmuxIO.read('list-panes').unsafe, self.tmux).must(have_length(1)))


__all__ = ('ClosePaneSpec',)
