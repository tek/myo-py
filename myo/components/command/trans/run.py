from amino import do, Do, Maybe, __, _, ADT, L
from amino.state import EitherState, State

from amino.dat import Dat
from amino.boolean import false
from amino.dispatch import PatMat

from ribosome.trans.api import trans
from ribosome.trans.handler import FreeTrans
from ribosome.plugin_state import PluginState
from ribosome.trans.action import TransM

from myo.util import Ident
from myo.config.component import MyoComponent
from myo.env import Env
from myo.settings import MyoSettings
from myo.config.handler import find_handler
from myo.data.command import Command, Interpreter, SystemInterpreter, ShellInterpreter, VimInterpreter
from myo.ui.data.view import Pane
from myo.components.ui.trans.pane import ui_pane_by_ident, render_pane
from myo.command.run_task import RunTask, UiSystemTask, UiShellTask


class RunCommandOptions(Dat['RunCommandOptions']):

    def __init__(
            self,
            interpreter: Maybe[str],
    ) -> None:
        self.interpreter = interpreter


def shell_task() -> TransM:
    pass


def system_task() -> TransM:
    pass


@do(TransM[RunTask])
def ui_system_task(cmd: Command, target: Ident) -> Do:
    # ensure_view
    pane = yield ui_pane_by_ident(target).m
    yield render_pane(pane.ident).m
    yield TransM.pure(UiSystemTask(cmd, pane))


class run_task(PatMat[Interpreter, TransM[RunTask]], alg=Interpreter):

    def __init__(self, cmd: Command) -> None:
        self.cmd = cmd

    @do(TransM[RunTask])
    def system_interpreter(self, interpreter: SystemInterpreter) -> Do:
        yield interpreter.target / L(ui_system_task)(self.cmd, _) | (lambda: system_task(self.cmd))

    @do(TransM[RunTask])
    def shell_interpreter(self, interpreter: ShellInterpreter) -> Do:
        print(interpreter)
        shell = yield State.inspect_f(__.comp.command_by_ident(interpreter.target)).trans
        target = yield TransM.from_maybe(shell.interpreter.target,
                                         f'shell `{shell.ident}` for command `{self.cmd.ident}` has no pane')
        pane = yield ui_pane_by_ident(target).m
        yield render_pane(pane.ident).m
        return UiShellTask(self.cmd, shell, pane)

    @do(TransM[RunTask])
    def vim_interpreter(self, interpreter: VimInterpreter) -> Do:
        pass


@trans.free.result(trans.st, component=false)
@do(EitherState[PluginState[MyoSettings, Env, MyoComponent], FreeTrans])
def run_handler(cmd: Command) -> Do:
    yield find_handler(__.can_run(cmd), _.run, str(cmd))


@trans.free.do()
@do(TransM)
def run_command(ident: Ident, options: RunCommandOptions) -> Do:
    cmd = yield EitherState.inspect_f(__.comp.command_by_ident(ident)).trans
    task = yield run_task(cmd)(cmd.interpreter)
    print(task)
    handler = yield run_handler(task).m
    yield handler(task).m
    # yield push_history(cmd, target).m


__all__ = ('run_command',)
