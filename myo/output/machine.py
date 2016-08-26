from ribosome.machine import message, may_handle, Machine
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine

from amino.task import Task

from myo.output.data import ParseResult
from myo.state import MyoTransitions
from myo.logging import Logging

OutputInit = message('OutputInit')


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



class OutputMachine(ScratchMachine, Logging):
    Transitions = OutputMachineTransitions

    def __init__(self, vim: NvimFacade, scratch: ScratchBuffer,
                 result: ParseResult, parent: Machine) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self.result = result

__all__ = ('OutputMachine',)
