from typing import Callable, Any, TypeVar

from ribosome.nvim.api import nvim_call_cons, current_cursor, cons_decode_str, cons_decode_str_list
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS
from ribosome.config.config import Resources
from ribosome.dispatch.component import ComponentData

from amino import _, Either, do, Do, Dat
from amino.json import encode_json

from myo.components.command.data import CommandData
from myo.settings import setting, MyoSettings
from myo.config.component import MyoComponent

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


@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], VimTestPosition])
def vim_test_position() -> Do:
    fn_mod = yield setting(_.vim_test_filename_modifier)
    file = yield NS.lift(nvim_call_cons(cons_decode_str, 'expand', f'%{fn_mod}'))
    line, col = yield NS.lift(current_cursor())
    return VimTestPosition(file, line, col)


@do(NvimIO[None])
def assemble_vim_test_line(position: VimTestPosition) -> Do:
    runner = yield vim_test_call_wrap(cons_decode_str, 'DetermineRunner', position.file)
    exe = yield vim_test_call_wrap(cons_decode_str, 'Executable', runner)
    pos_json = yield NvimIO.from_either(encode_json(position))
    pre_args = yield vim_test_call_wrap(cons_decode_str_list, f'BuildPosition', runner, pos_json.native)
    args = yield vim_test_call_wrap(cons_decode_str_list, f'BuildArgs', runner, pre_args)
    return args.cons(exe).join_tokens


@do(NS[Resources[ComponentData[D, CommandData], MyoSettings, MyoComponent], None])
def vim_test_line() -> Do:
    position = yield vim_test_position()
    yield NS.lift(assemble_vim_test_line(position))


__all__ = ('vim_test_line', 'test_determine_runner', 'test_executable', 'build_position', 'build_args')
