from typing import Any, Tuple

from kallikrein import k, Expectation, pending

from amino.test.spec import SpecBase
from amino import Map, Nil, List, Either, Left, Right, do, Do

from ribosome.config.config import Config
from ribosome.compute.run import run_prog
from ribosome.nvim.api.data import StrictNvimApi
from ribosome import NvimApi
from ribosome.test.config import TestConfig
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.test.unit import unit_test

from myo.env import Env
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.components.ui.compute.init import init


config: Config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(ui=ui, tmux=tmux),
)


def req_handler(vim: StrictNvimApi, name: str, args: List[Any]) -> Either[List[str], Tuple[NvimApi, Any]]:
    if name == 'nvim_call_function':
        if args.head.contains('getpid'):
            return Right((vim, 1991))
    return Left(Nil)


test_config = TestConfig.cons(config, components=List('ui', 'tmux'), request_handler=req_handler)


@do(NS[PS, Expectation])
def init_spec() -> Do:
    yield run_prog(init, Nil)
    return k(1) == 1


class UiInitSpec(SpecBase):
    '''
    initialize the ui component $init
    '''

    @pending
    def init(self) -> Expectation:
        return unit_test(test_config, init_spec)


__all__ = ('UiInitSpec',)
