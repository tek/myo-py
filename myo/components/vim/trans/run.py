from ribosome.trans.api import trans
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS

from amino import do, Do, Boolean
from amino.boolean import true

from myo.data.command import Command
from myo.env import Env
from myo.command.run_task import RunTask, VimTask


@trans.free.unit(trans.st)
@do(NS[Env, None])
def run_command(task: VimTask) -> Do:
    cmd = task.command
    yield NS.lift(cmd.lines.traverse(lambda a: NvimIO.cmd_sync(a, verbose=~cmd.interpreter.silent), NvimIO))
    yield NS.unit


def vim_can_run(task: RunTask) -> Boolean:
    return isinstance(task, VimTask)


__all__ = ('run_command', 'vim_can_run')
