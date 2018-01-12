from ribosome.trans.api import trans
from ribosome.plugin_state import PluginState
from ribosome.nvim import NvimIO
from ribosome.nvim.io import NS

from amino import do, Do, Boolean, __
from amino.boolean import true

from myo.util import Ident
from myo import MyoSettings, Env, MyoComponent
from myo.data.command import Command


@trans.free.unit(trans.st)
@do(NS[PluginState[MyoSettings, Env, MyoComponent], None])
def run_command(ident: Ident) -> Do:
    cmd = yield NS.inspect_f(__.main.data.command_by_ident(ident))
    yield NS.lift(cmd.lines.traverse(lambda a: NvimIO.cmd_sync(a, verbose=~cmd.interpreter.silent), NvimIO))
    yield NS.pure(None)


def vim_can_run(cmd: Command) -> Boolean:
    return true


__all__ = ('run_command', 'vim_can_run')
