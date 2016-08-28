from operator import add

from ribosome.machine import message, may_handle, Machine, handle
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine

from amino.task import Task
from amino import Map, _, L, Left, __

from myo.output.data import ParseResult
from myo.state import MyoTransitions
from myo.logging import Logging
from myo.output.parser.python import FileEntry

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

    @handle(Jump)
    def jump(self):
        target = (
            self.vim.window.line /
            (_ - 1) //
            self.result.target_for_line
        ).filter_type(FileEntry).to_either('not a file entry')
        open_file = target / L(self._open_file)(_.path)
        set_line = (target / _.line /
                    (lambda a: Task(lambda: self.vim.window.set_cursor(a))))
        return (open_file & set_line).map2(add)

    def _open_file(self, path):
        def split():
            # TODO
            pass
        if not path.is_file():
            return Task.now(Left('not a file: {}'.format(path)))
        else:
            win = (
                self.vim.windows.find(__.buffer.modifiable.contains(True))
                .or_else(split)
                .task('could not get a window') /
                __.focus()
            )
            edit = Task.call(self.vim.edit, path) / __.run_async()
            return win + edit


class OutputMachine(ScratchMachine, Logging):
    Transitions = OutputMachineTransitions

    def __init__(self, vim: NvimFacade, scratch: ScratchBuffer,
                 result: ParseResult, parent: Machine) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self.result = result

    @property
    def prefix(self):
        return 'Myo'

    @property
    def mappings(self):
        special = {
            '%cr%': Jump,
        }
        return Map(**special)

__all__ = ('OutputMachine',)
