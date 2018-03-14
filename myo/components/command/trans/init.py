from amino import do, Do, List
from amino.util.string import camelcase

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome import ribo_log
from ribosome.nvim.api import define_function
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS

from myo.components.core.data import CoreData
from myo.env import Env


def vim_test_wrapper(name: str, params: List[str]) -> NvimIO[None]:
    args = params.map(lambda a: f'a:{a}')
    return define_function(f'MyoTest{camelcase(name)}', params, f'return test#{name}({args.join_comma})')


@do(NvimIO[None])
def define_vim_test_wrappers() -> Do:
    yield vim_test_wrapper('determine_runner', List('file'))
    yield define_function('MyoTestExecutable', List('runner'), 'return test#{runner}#executable()')
    yield vim_test_wrapper('build_position', List('runner', 'pos'))
    yield vim_test_wrapper('build_args', List('runner', 'args'))


@trans.free.unit(trans.st)
@do(NS[ComponentData[Env, CoreData], None])
def stage1() -> Do:
    r = yield NS.lift(define_vim_test_wrappers())
    yield NS.unit


@trans.free.result(trans.st)
@do(NS[None, None])
def test_determine_runner(file: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, 'determine_runner', file))


@trans.free.result(trans.st)
@do(NS[None, None])
def test_executable(runner: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, f'{runner}#executable'))


@trans.free.result(trans.st)
@do(NS[None, None])
def build_position(runner: str, pos: dict) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'base#build_position', runner, pos))


@trans.free.result(trans.st)
@do(NS[None, None])
def build_args(runner: str, args: list) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'base#build_args', runner, args))


__all__ = ('stage1',)
