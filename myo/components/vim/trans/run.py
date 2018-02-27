from ribosome.trans.api import trans
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS

from amino import do, Do, Boolean

from myo.env import Env
from myo.command.run_task import RunTask, VimTaskDetails


@trans.free.unit(trans.st)
@do(NS[Env, None])
def run_command(task: RunTask) -> Do:
    cmd = task.command
    yield NS.lift(cmd.lines.traverse(lambda a: NvimIO.cmd_sync(a, verbose=~cmd.interpreter.silent), NvimIO))
    yield NS.unit


def vim_can_run(task: RunTask) -> Boolean:
    return isinstance(task.details, VimTaskDetails)


__all__ = ('run_command', 'vim_can_run')
