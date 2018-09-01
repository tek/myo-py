from amino import List, do, Do

from ribosome.nvim.api.command import nvim_command_output
from ribosome.nvim.io.compute import NvimIO


def myo_syntax_items(lines: List[str]) -> List[str]:
    return lines.filter(lambda a: a.startswith('Myo')).rstrip


@do(NvimIO[List[str]])
def myo_syntax() -> Do:
    syntax = yield nvim_command_output('syntax')
    return myo_syntax_items(syntax)


@do(NvimIO[List[str]])
def myo_highlight() -> Do:
    syntax = yield nvim_command_output('highlight')
    return myo_syntax_items(syntax)


__all__ = ('myo_syntax_items', 'myo_syntax', 'myo_highlight',)
