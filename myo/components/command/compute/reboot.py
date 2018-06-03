from typing import TypeVar, Generic

from amino import do, Do, Maybe, Nothing
from amino.case import Case

from ribosome.compute.api import prog

from chiasma.util.id import IdentSpec, Ident
from ribosome.nvim.io.state import NS
from ribosome.compute.ribosome_api import Ribo

from myo.components.command.compute.tpe import CommandRibosome
from myo.util.id import ensure_ident_ns
from myo.components.command.data import CommandData
from myo.components.command.compute.run import run_command, command_by_ident, run_command_1
from myo.data.command import Command, Interpreter, SystemInterpreter
from myo.components.ui.compute.close_pane import close_pane

D = TypeVar('D')


class target_pane(Generic[D], Case[Interpreter, Maybe[Ident]], alg=Interpreter):

    def system_interpreter(self, interpreter: SystemInterpreter) -> Maybe[Ident]:
        return interpreter.target

    def case_default(self, interpreter: Interpreter) -> Maybe[Ident]:
        return Nothing


@prog.do(None)
def reboot_command_pane(cmd: Command) -> Do:
    pane = target_pane.match(cmd.interpreter)
    yield pane.cata(close_pane, NS.unit)
    yield run_command_1(cmd)


@prog.do(None)
def reboot(ident_spec: IdentSpec) -> Do:
    ident = yield Ribo.lift_comp(ensure_ident_ns(ident_spec), CommandData)
    cmd = yield command_by_ident(ident)
    yield reboot_command_pane(cmd)


__all__ = ('reboot',)
