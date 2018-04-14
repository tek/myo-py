from typing import Any, Tuple

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import Map, Nil, List, Either, Left, Right

from ribosome.test.integration.run import RequestHelper
from ribosome.config.config import Config
from ribosome.compute.run import run_prog
from ribosome.nvim.api.data import StrictNvimApi
from ribosome import NvimApi

from myo.env import Env
from myo.components.tmux.config import tmux
from myo.components.ui.config import ui
from myo.components.ui.compute.init import init
from myo.settings import MyoSettings


config: Config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(ui=ui, tmux=tmux),
    settings=MyoSettings(),
)


def req_handler(vim: StrictNvimApi, name: str, args: List[Any]) -> Either[List[str], Tuple[NvimApi, Any]]:
    if name == 'nvim_call_function':
        if args.head.contains('getpid'):
            return Right((vim, 1991))
    return Left(Nil)


class UiInitSpec(SpecBase):
    '''
    initialize the ui component $init
    '''

    def init(self) -> Expectation:
        helper = RequestHelper.strict(config, 'ui', 'tmux', request_handler=req_handler)
        r = run_prog(init, Nil).run(helper.state).run(helper.vim)
        return k(1) == 1


__all__ = ('UiInitSpec',)
