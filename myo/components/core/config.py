from amino import List

from ribosome.config.component import Component
from ribosome.request.handler.handler import RequestHandler
from ribosome.request.handler.prefix import Plain

from myo.components.core.compute.init import init
from myo.components.core.data import CoreData
from myo.components.core.compute.info import info
from myo.components.core.compute.vim_leave import vim_leave


core = Component.cons(
    'core',
    state_type=CoreData,
    request_handlers=List(
        RequestHandler.trans_cmd(init)(),
        RequestHandler.trans_cmd(info)(),
        RequestHandler.trans_autocmd(vim_leave)(prefix=Plain()),
    ),
)

__all__ = ('core',)
