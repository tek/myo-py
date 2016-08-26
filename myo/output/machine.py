from ribosome.machine import message, may_handle, Machine
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine

from amino.task import Task
from amino import Map, _

from myo.output.data import ParseResult
from myo.state import MyoTransitions
from myo.logging import Logging

OutputInit = message('OutputInit')
Jump = message('Jump')


class OutputMachineTransitions(MyoTransitions):

    @property
    def scratch(self):
        return self.machine.scratch

    @property
    def buffer(self):
        return self.scratch.buffer

    @property
    def result(self):
        return self.machine.result

    @may_handle(OutputInit)
    def output_init(self):
        return (
            Task.call(self.buffer.set_content, self.result.display_lines) //
            (lambda a: Task.call(self.buffer.set_modifiable, False))
        )

    @may_handle(Jump)
    def jump(self):
        entry = self.vim.window.line / (_ - 1) // self.result.target_for_line


class OutputMachine(ScratchMachine, Logging):
    Transitions = OutputMachineTransitions

    def __init__(self, vim: NvimFacade, scratch: ScratchBuffer,
                 result: ParseResult, parent: Machine) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self.result = result

    @property
    def mappings(self):
        special = {
            '%cr%': Jump,
        }
        return Map(**special)

__all__ = ('OutputMachine',)
