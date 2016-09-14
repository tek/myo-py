from operator import add

from ribosome.machine import message, may_handle, Machine, handle, Nop
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine, Quit
from ribosome.machine.base import UnitTask
from ribosome.machine.state import Init
from ribosome.record import field

from amino.task import Task
from amino import Map, _, L, Left, __, List, Either, Just
from amino.lazy import lazy

from myo.output.data import ParseResult, Location
from myo.state import MyoTransitions
from myo.logging import Logging
from myo.record import Record
from myo.util import parse_callback_spec

Jump = message('Jump')
FirstError = message('FirstError')
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

    @property
    def langs(self):
        return self.result.langs

    @property
    def events(self):
        return self.result.events


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

    @property
    def _special_jumps(self):
        return Map(default=self._jump_default, first=self._jump_first,
                   last=self._jump_last)

    @property
    def _lang_jumps(self):
        return Map(python=self._jump_last)

    @may_handle(Init)
    def init(self):
        return self.with_sub(self.state), DisplayLines()

    @handle(DisplayLines)
    def display_lines(self):
        def run(lines):
            return (
                Task.call(self.buffer.set_content, lines) &
                Task.call(self.buffer.set_modifiable, False)
            ).replace(Just(FirstError()))
        return self.result.display_lines / run

    @handle(FirstError)
    def first_error(self):
        spec = (
            self.machine.options.get('first_error')
            .o(self.vim.vars.pl('first_error')) |
            List()
        ).cat('default')
        special, custom_spec = spec.split(self._special_jumps.contains)
        special_cb = special // self._special_jumps.get
        jump = self.vim.vars.pb('jump_to_error') | True
        next_step = Jump() if jump else Nop()
        return (
            (
                custom_spec /
                parse_callback_spec /
                _.ljoin
            ).sequence(Either) // (
                __
                .add(special_cb)
                .find_map(__(self.result))
                .map2(L(Task.call)(self.vim.window.set_cursor, _, _))
                .map(__.replace(Just(next_step)))
            )
        )

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

    @property
    def _jump_default(self):
        return (self.result.langs.find_map(self._lang_jumps.get) |
                (lambda: self._jump_first))

    def _position_index(self, lines):
        return (
            lines
            .index_where(lambda a: isinstance(a.target, Location))
            .map(lambda a: (a + 1, 1))
        )

    def _jump_first(self, result):
        return (self.result.lines // self._position_index)

    def _jump_last(self, result):
        def run(lines):
            return (
                self._position_index(lines)
                .map2(lambda l, c: (lines.length - l, c))
            )
        return self.result.lines / _.reversed // run

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
                 result: ResultAdapter, parent: Machine, options: Map) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self.result = result
        self.options = options

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
