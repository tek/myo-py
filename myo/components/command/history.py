from amino import do, Do

from ribosome.trans.api import trans
from ribosome.nvim.io import NS

from myo import Env


@trans.free.unit(trans.st)
@do(NS[Env, None])
def load_history() -> Do:
    pass

__all__ = ('load_history',)
