from ribosome.trans.api import trans
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS

from amino import do, Do, Boolean
from amino.boolean import true

from myo.data.command import Command
from myo.env import Env


@trans.free.unit(trans.st)
@do(NS[Env, None])
def run_command(cmd: Command) -> Do:
    yield NS.lift(cmd.lines.traverse(lambda a: NvimIO.cmd_sync(a, verbose=~cmd.interpreter.silent), NvimIO))
    yield NS.unit


def vim_can_run(cmd: Command) -> Boolean:
    return true


__all__ = ('run_command', 'vim_can_run')
