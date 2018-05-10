from amino import List

from ribosome.config.component import Component
from ribosome.rpc.api import rpc
from ribosome.rpc.data.prefix_style import Plain

from myo.components.core.compute.init import init
from myo.components.core.data import CoreData
from myo.components.core.compute.info import info
from myo.components.core.compute.vim_leave import vim_leave


core = Component.cons(
    'core',
    state_type=CoreData,
    rpc=List(
        rpc.write(init),
        rpc.write(info),
        rpc.autocmd(vim_leave).conf(prefix=Plain()),
    ),
)

__all__ = ('core',)
