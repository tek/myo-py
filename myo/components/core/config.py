from amino import List

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from myo.components.core.trans.init import init
from myo.components.core.data import CoreData


core = Component.cons(
    'core',
    state_ctor=CoreData.cons,
    request_handlers=List(
        RequestHandler.trans_cmd(init)(),
    ),
)

__all__ = ('core',)
