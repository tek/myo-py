from ribosome.machine import message, may_handle, Machine
from ribosome.nvim import ScratchBuffer, NvimFacade

from amino.task import Task

from myo.output.data import ParseResult
from myo.state import MyoTransitions, MyoComponent

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


class OutputMachine(MyoComponent):
    Transitions = OutputMachineTransitions

    def __init__(self, vim: NvimFacade, scratch: ScratchBuffer,
                 result: ParseResult, parent: Machine) -> None:
        super().__init__(vim, parent=parent, title='output')
        self.scratch = scratch
        self.result = result

__all__ = ('OutputMachine',)
