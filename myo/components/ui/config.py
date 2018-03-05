from amino import List
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Full

from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData
from myo.components.ui.trans.open_pane import open_pane
from myo.components.ui.trans.close_pane import close_pane
from myo.components.ui.trans.minimize_pane import minimize_pane
from myo.components.ui.trans.pane import ui_pane_by_ident, render_pane, pane_owners
from myo.components.ui.trans.create_pane import create_pane
from myo.components.ui.trans.init import stage1


ui = Component.cons(
    'ui',
    state_ctor=UiData.cons,
    request_handlers=List(
        RequestHandler.trans_cmd(create_pane)(json=true),
        RequestHandler.trans_cmd(open_pane)(json=true),
        RequestHandler.trans_cmd(close_pane)(),
        RequestHandler.trans_cmd(minimize_pane)(),
        RequestHandler.trans_function(ui_pane_by_ident)(),
        RequestHandler.trans_function(render_pane)(),
        RequestHandler.trans_function(pane_owners)(),
        RequestHandler.trans_cmd(stage1)(prefix=Full()),
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(),
)

__all__ = ('ui',)
