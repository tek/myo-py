from amino import do, Do, List
from amino.util.string import camelcase

from ribosome.compute.api import prog
from ribosome.config.component import ComponentData
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.state import NS
from ribosome.nvim.api.function import define_function

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


@prog.unit
@do(NS[ComponentData[Env, CoreData], None])
def init() -> Do:
    r = yield NS.lift(define_vim_test_wrappers())
    yield NS.unit


@prog
@do(NS[None, None])
def test_determine_runner(file: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, 'determine_runner', file))


@prog
@do(NS[None, None])
def test_executable(runner: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, f'{runner}#executable'))


@prog
@do(NS[None, None])
def build_position(runner: str, pos: dict) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'base#build_position', runner, pos))


@prog
@do(NS[None, None])
def build_args(runner: str, args: list) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'base#build_args', runner, args))


__all__ = ('init',)
