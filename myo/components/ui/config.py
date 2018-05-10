from amino import List
from amino.boolean import true

from ribosome.config.component import Component
from ribosome.rpc.data.prefix_style import Full
from ribosome.rpc.api import rpc

from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData
from myo.components.ui.compute.open_pane import open_pane
from myo.components.ui.compute.close_pane import close_pane
from myo.components.ui.compute.minimize_pane import minimize_pane
from myo.components.ui.compute.pane import ui_pane_by_ident, render_pane, pane_owners
from myo.components.ui.compute.create_pane import create_pane
from myo.components.ui.compute.init import init
from myo.components.ui.compute.info import ui_info


ui = Component.cons(
    'ui',
    state_type=UiData,
    rpc=List(
        rpc.write(create_pane).conf(json=true),
        rpc.write(open_pane).conf(json=true),
        rpc.write(close_pane),
        rpc.write(minimize_pane),
        rpc.write(ui_pane_by_ident),
        rpc.write(render_pane),
        rpc.write(pane_owners),
        rpc.write(init).conf(prefix=Full()),
        rpc.write(ui_info),
    ),
    config=MyoComponent.cons(info=ui_info, init=init),
)

__all__ = ('ui',)
