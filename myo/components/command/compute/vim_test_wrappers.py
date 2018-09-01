from amino import do, Do, List
from amino.logging import module_log

from ribosome.compute.api import prog
from ribosome.nvim.io.state import NS
from ribosome.nvim.api.util import cons_decode_str, cons_decode_str_list

from myo.components.command.compute.vim_test import vim_test_call

log = module_log()


@prog
@do(NS[None, str])
def test_determine_runner(file: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, 'determine_runner', file))


@prog
@do(NS[None, str])
def test_executable(runner: str) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str, f'{runner}#executable'))


@prog
@do(NS[None, List[str]])
def test_build_position(runner: str, pos: dict) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'{runner}#build_position', 'nearest', pos))


@prog
@do(NS[None, str])
def test_build_args(runner: str, args: list) -> Do:
    yield NS.lift(vim_test_call(cons_decode_str_list, f'{runner}#build_args', args))


__all__ = ('init',)
