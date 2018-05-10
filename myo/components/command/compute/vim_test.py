from typing import Callable, Any, TypeVar

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.state import NS
from ribosome.nvim.api.function import nvim_call_cons
from ribosome.nvim.api.ui import current_cursor
from ribosome.nvim.api.util import cons_decode_str, cons_decode_str_list
from ribosome.nvim.io.api import N
from ribosome.compute.ribosome_api import Ribo

from amino import _, Either, do, Do, Dat
from amino.json import encode_json

from myo.components.command.compute.tpe import CommandRibosome
from myo.settings import vim_test_filename_modifier

A = TypeVar('A')
D = TypeVar('D')


def vim_test_call(cons: Callable[[Any], Either[str, A]], fun: str, *args: str) -> NvimIO[str]:
    return nvim_call_cons(cons, f'test#{fun}', *args)


def vim_test_call_wrap(cons: Callable[[Any], Either[str, A]], fun: str, *args: str) -> NvimIO[str]:
    return nvim_call_cons(cons, f'MyoTest{fun}', *args)


class VimTestPosition(Dat['VimTestPosition']):

    def __init__(self, file: str, line: str, col: str) -> None:
        self.file = file
        self.line = line
        self.col = col


@do(NS[CommandRibosome, VimTestPosition])
def vim_test_position() -> Do:
    fn_mod = yield Ribo.setting(vim_test_filename_modifier)
    file = yield NS.lift(nvim_call_cons(cons_decode_str, 'expand', f'%{fn_mod}'))
    line, col = yield NS.lift(current_cursor())
    return VimTestPosition(file, line, col)


@do(NvimIO[None])
def assemble_vim_test_line(position: VimTestPosition) -> Do:
    runner = yield vim_test_call_wrap(cons_decode_str, 'DetermineRunner', position.file)
    exe = yield vim_test_call_wrap(cons_decode_str, 'Executable', runner)
    pos_json = yield N.from_either(encode_json(position))
    pre_args = yield vim_test_call_wrap(cons_decode_str_list, f'BuildPosition', runner, pos_json.native)
    args = yield vim_test_call_wrap(cons_decode_str_list, f'BuildArgs', runner, pre_args)
    return args.cons(exe).join_tokens


@do(NS[CommandRibosome, None])
def vim_test_line() -> Do:
    position = yield vim_test_position()
    yield NS.lift(assemble_vim_test_line(position))


__all__ = ('vim_test_line', 'test_determine_runner', 'test_executable', 'build_position', 'build_args')
