from kallikrein import Expectation, kf
from kallikrein.matchers.length import have_length

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.data.view_tree import ViewTree
from chiasma.ui.view_geometry import ViewGeometry
from chiasma.io.compute import TmuxIO
from chiasma.data.pane import Pane as TPane
from chiasma.commands.pane import all_panes, pane

from amino import List, __, L, _
from amino.boolean import true
from amino.lenses.lens import lens

from ribosome.test.integration.klk import later

from myo.ui.data.view import Layout, Pane
from myo.ui.pane import map_panes_in_spaces

from unit._support.tmux import init_tmux_data


class MinimizePaneSpec(TmuxSpec):
    '''
    minimize a tmux pane $minimize_pane
    '''

    def minimize_pane(self) -> Expectation:
        layout = ViewTree.layout(
            Layout.cons('root', vertical=true),
            List(
                ViewTree.pane(Pane.cons('one', geometry=ViewGeometry.cons())),
                ViewTree.pane(Pane.cons('two', geometry=ViewGeometry.cons())),
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
        helper1.loop('command:minimize_pane', args=('one',)).unsafe(helper.vim)
        return later(kf(lambda: pane(0, 0).unsafe(self.tmux).height) == 2)


__all__ = ('MinimizePaneSpec',)
