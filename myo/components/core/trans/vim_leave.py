from amino import do, Do, _

from ribosome.trans.handler import Trans
from ribosome.trans.api import trans
from ribosome import ribo_log

from myo.config.handler import find_handlers


@trans.free.do()
@do(Trans[None])
def vim_leave() -> Do:
    handlers = yield find_handlers(_.quit)
    yield handlers.sequence(Trans)


__all__ = ('vim_leave',)
