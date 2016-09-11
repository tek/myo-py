from operator import add

from ribosome.machine import message, may_handle, Machine, handle
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine, Quit
from ribosome.machine.base import UnitTask
from ribosome.machine.state import Init
from ribosome.record import field

from amino.task import Task
from amino import Map, _, L, Left, __, List, Either
from amino.lazy import lazy

from myo.output.data import ParseResult, Location
from myo.state import MyoTransitions
from myo.logging import Logging
from myo.record import Record
from myo.util import parse_callback_spec

Jump = message('Jump')
DisplayLines = message('DisplayLines')


class ResultAdapter(Logging):

    def __init__(self, vim, result: ParseResult, filters: List[str]) -> None:
        self.vim = vim
        self.result = result
        self.filters = filters

    @property
    def filter_callbacks(self):
        return (
            self.filters / parse_callback_spec / __.right_or_map(Left)
        ).sequence(Either)

    @lazy
    def lines(self):
        def fold(cbs):
            return cbs.fold_left(self.result.lines)(lambda z, a: a(z))
        return self.filter_callbacks / fold

    @property
    def display_lines(self):
        return (self.lines.eff() / _.text).value

    def target_for_line(self, line):
        return self.lines // __.lift(line) / _.target


class OMState(Record):
    result = field(ResultAdapter)


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

    @may_handle(Init)
    def init(self):
        return self.with_sub(self.state), DisplayLines()

    @handle(DisplayLines)
    def display_lines(self):
        return self.result.display_lines / (lambda a: UnitTask(
            Task.call(self.buffer.set_content, a) //
            (lambda a: Task.call(self.buffer.set_modifiable, False))
        ))

    @handle(Jump)
    def jump(self):
        target = (
            self.vim.window.line /
            (_ - 1) //
            self.result.target_for_line
        ).filter_type(Location).to_either('not a location')
        open_file = target / L(self._open_file)(_.file_path)
        set_line = (
            (target / _.coords)
            .map2(lambda a, b: Task(lambda: self.vim.window.set_cursor(a, b)))
        )
        return (open_file & set_line).map2(add) / UnitTask

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
                 result: ResultAdapter, parent: Machine) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self.result = result

    @property
    def prefix(self):
        return 'Myo'

    @property
    def mappings(self):
        return Map({
            '%cr%': Jump,
            'q': Quit,
        })

    def new_state(self):
        return OMState(result=self.result)

__all__ = ('OutputMachine',)
