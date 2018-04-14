from amino import List
from amino.boolean import true

from ribosome.config.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Full

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
    request_handlers=List(
        RequestHandler.trans_cmd(create_pane)(json=true),
        RequestHandler.trans_cmd(open_pane)(json=true),
        RequestHandler.trans_cmd(close_pane)(),
        RequestHandler.trans_cmd(minimize_pane)(),
        RequestHandler.trans_function(ui_pane_by_ident)(),
        RequestHandler.trans_function(render_pane)(),
        RequestHandler.trans_function(pane_owners)(),
        RequestHandler.trans_cmd(init)(prefix=Full()),
        RequestHandler.trans_function(ui_info)(),
    ),
    config=MyoComponent.cons(info=ui_info, init=init),
)

__all__ = ('ui',)
