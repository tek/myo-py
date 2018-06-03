from ribosome.compute.api import prog
from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.io.state import NS
from ribosome.nvim.api.command import nvim_command

from amino import do, Do, Boolean

from myo.env import Env
from myo.command.run_task import RunTask, VimTaskDetails


@prog.unit
@do(NS[Env, None])
def run(task: RunTask) -> Do:
    cmd = task.command
    yield NS.lift(cmd.lines.traverse(lambda a: nvim_command(a, verbose=~cmd.interpreter.silent), NvimIO))
    yield NS.unit


def vim_can_run(task: RunTask) -> Boolean:
    return isinstance(task.details, VimTaskDetails)


__all__ = ('run', 'vim_can_run')
