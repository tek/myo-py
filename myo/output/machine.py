from operator import add
from typing import Callable

from ribosome.machine import message, may_handle, Machine, handle, Nop
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine, Quit
from ribosome.machine.base import UnitTask
from ribosome.machine.state import Init
from ribosome.record import field, list_field

from amino.task import Task
from amino import Map, _, L, Left, __, List, Either, Just, Try, Right, Boolean
from amino.lazy import lazy

from myo.output.data import ParseResult, Location, OutputLine
from myo.state import MyoTransitions, MyoHelpers
from myo.logging import Logging
from myo.record import Record
from myo.util.callback import SpecialCallback
from myo.output.reifier.base import Reifier, LiteralReifier
from myo.output.syntax.base import LineGroups

Jump = message('Jump')
FirstError = message('FirstError')
DisplayLines = message('DisplayLines')


def fold_callbacks(cbs, z):
    return cbs.fold_left(Right(z))(lambda z, a: z // L(Try)(a, _))


class ResultAdapter(Logging):

    def __init__(self, buffer, result: ParseResult, filters: List[Callable],
                 reifier: Either[str, Reifier], formatters: List[Callable],
                 syntaxes: List[Callable], first_error: List[Callable]
                 ) -> None:
        self.buffer = buffer
        self.result = result
        self.filters = filters
        self.reifier = reifier
        self.formatters = formatters
        self.syntaxes = syntaxes
        self.first_error = first_error

    @lazy
    def vim(self):
        return self.buffer.root

    @property
    def filtered(self):
        return fold_callbacks(self.filters, self.result)

    def format(self, lines: List[OutputLine]):
        return fold_callbacks(self.formatters, lines)

    @property
    def _reifier(self):
        return (
            self.reifier.o(lambda: self._lang_reifier) |
            (lambda: LiteralReifier(self.buffer))
        )

    @property
    def _lang_reifier(self):
        want = self.vim.vars.pb('lang_reifier') | Boolean(True)
        def create(lang):
            return (
                Either.import_name('myo.output.reifier.{}'.format(lang),
                                   'Reifier')
            )
        return want.maybe(self.langs) // __.find_map(create) / __(self.buffer)

    @property
    def lines(self):
        return self.filtered // L(Try)(self._reifier, _) // self.format

    @property
    def langs(self):
        return self.result.langs

    @property
    def events(self):
        return self.result.events

    def __repr__(self):
        return repr(self.result)


class OMState(Record):
    result = field(ResultAdapter)
    lines = list_field(OutputLine)


class OutputMachineTransitions(MyoTransitions):

    @property
    def scratch(self):
        return self.machine.scratch

    @property
    def buffer(self):
        return self.scratch.buffer

    @property
    def window(self):
        return self.scratch.window

    @property
    def result(self):
        return self.state.result

    @property
    def _special_jumps(self):
        return Map(default=self._jump_default, first=self._jump_first,
                   last=self._jump_last)

    @property
    def _lang_jumps(self):
        return Map(python=self._jump_last)

    @property
    def lines(self):
        return self.state.lines

    @property
    def _set_content(self):
        min_size = self.vim.vars.pi('output_window_min_size') | 10
        max_size = self.vim.vars.pi('output_window_max_size') | 30
        def run(lines):
            text = lines / _.formatted
            size = min(max_size, max(min_size, text.length))
            return (
                self._with_sub(self.data, self.state.set(lines=lines)),
                Task.call(self.window.cmd, 'resize {}'.format(size)) +
                Task.call(self.buffer.set_content, text) +
                Task.call(self.buffer.set_modifiable, False) +
                self._run_syntax(lines)
            )
        return self.result.lines / run

    @property
    def _syntax(self):
        lang = self._lang_syntax.to_list
        return self.result.syntaxes.cons(LineGroups(self.vim)) + lang

    @property
    def _lang_syntax(self):
        def create(lang):
            return Either.import_name('myo.output.syntax.{}'.format(lang),
                                      'Syntax')
        return self.result.langs.find_map(create) / __(self.vim)

    def _run_syntax(self, lines):
        return (self._syntax / (lambda a: a(lines))).sequence(Task)

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

    @may_handle(Init)
    def init(self):
        return self.with_sub(self.state), DisplayLines()

    @handle(DisplayLines)
    def display_lines(self):
        return self._set_content.map2(
            lambda a, b: (a, b.replace(Just(FirstError()))))

    @handle(FirstError)
    def first_error(self):
        def set_cursor(a):
            x, y = a if isinstance(a, tuple) else (a, 1)
            return Task(lambda: self.vim.window.set_cursor(x + 1, y))
        special, custom = self.result.first_error.split_type(SpecialCallback)
        special_cb = special / _.name // self._special_jumps.get
        jump = self.vim.vars.pb('jump_to_error') | True
        next_step = Jump() if jump else Nop()
        return (
            (custom + special_cb)
            .find_map(__(self.lines))
            .map(set_cursor)
            .map(__.replace(Just(next_step)))
        )

    @handle(Jump)
    def jump(self):
        # cannot use Task.call for set_cursor because then the window is fixed
        # to what is active before opening the file
        target = (
            self.vim.window.line /
            (_ - 1) //
            self.target_for_line
        ).filter_type(Location).to_either('not a location')
        open_file = target / L(self._open_file)(_.file_path)
        set_line = (
            (target / _.coords)
            .map2(lambda a, b: Task(lambda: self.vim.window.set_cursor(a, b)))
        )
        post = Task(lambda: self.vim.cmd('normal! zvzz'))
        return (open_file & set_line).map2(add) / (_ + post) / UnitTask

    @property
    def _jump_default(self):
        return (self.result.langs.find_map(self._lang_jumps.get) |
                (lambda: self._jump_first))

    def _location_index(self, lines):
        return (
            lines
            .index_where(__.entry.exists(L(isinstance)(_, Location)))
            .map(lambda a: (a + 1, 1))
        )

    def _jump_first(self, result):
        return self._location_index(self.lines)

    def _jump_last(self, result):
        return (
            self._location_index(self.lines.reversed)
            .map2(lambda l, c: (self.lines.length - l, c))
        )

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


class OutputMachine(ScratchMachine, MyoHelpers, Logging):
    Transitions = OutputMachineTransitions

    def __init__(self, vim: NvimFacade, scratch: ScratchBuffer,
                 result: ParseResult, parent: Machine, options: Map) -> None:
        super().__init__(vim, scratch, parent=parent, title='output')
        self._result = result
        self._options = options

    @property
    def options(self):
        return self._options

    @property
    def result(self):
        buffer = self.scratch.buffer
        filters = self._callbacks('output_filters')
        reifier = self._callback('output_reifier')
        formatters = self._callbacks('output_formatters')
        syntaxes = self._callbacks('output_syntaxes', buffer)
        first_error = (self._callbacks('first_error')
                       .cat(SpecialCallback('default')))
        return ResultAdapter(buffer, self._result, filters, reifier,
                             formatters, syntaxes, first_error)

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
