from amino import List
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from myo.config.component import MyoComponent
from myo.ui.data.ui_data import UiData
from myo.components.ui.trans.open_pane import open_pane


ui = Component.cons(
    'ui',
    state_ctor=UiData.cons,
    request_handlers=List(
        RequestHandler.trans_cmd(open_pane)(json=true),
    ),
    handlers=List(
    ),
    config=MyoComponent.cons(),
)

__all__ = ('ui',)
