from typing import Any, Tuple

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import Map, Nil, List, Either, Left, Right, do, Do

from ribosome.nvim.api.data import StrictNvimApi
from ribosome import NvimApi
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.config import TestConfig
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from myo import myo_config


def req_handler(vim: StrictNvimApi, name: str, args: List[Any]) -> Either[List[str], Tuple[NvimApi, Any]]:
    if name == 'nvim_call_function':
        if args.head.contains('getpid'):
            return Right((vim, 1991))
    return Left(Nil)


vars = Map(myo_vim_tmux_pane=0)
test_config = TestConfig.cons(
    myo_config,
    request_handler=req_handler,
    vars=vars,
    components=List('ui', 'tmux', 'core', 'command'),
)


@do(NS[PS, Expectation])
def init_spec() -> Do:
    yield request('init')
    return k(1) == 1


class InitSpec(SpecBase):
    '''
    initialize all components $init
    '''

    def init(self) -> Expectation:
        return unit_test(test_config, init_spec)


__all__ = ('InitSpec',)
