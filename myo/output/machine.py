from ribosome.machine import may_handle, Machine, handle, Nop
from ribosome.nvim import ScratchBuffer, NvimFacade
from ribosome.machine.scratch import ScratchMachine, Quit
from ribosome.machine.base import UnitTask
from ribosome.record import (field, list_field, either_field, any_field,
                             bool_field, dfield)
from ribosome.machine.transition import Fatal

from amino.task import Task
from amino import (Map, _, L, Left, __, List, Either, Just, Try, Right,
                   Boolean, Empty)
from amino.lazy import lazy

from myo.output.data import ParseResult, Location, OutputLine
from myo.state import MyoTransitions
from myo.logging import Logging
from myo.record import Record
from myo.output.reifier.base import Reifier, LiteralReifier
from myo.output.syntax.base import LineGroups
from myo.output.filter.base import DuplicatesFilter
from myo.output.message import (JumpCurrent, JumpCursor, Jump, SetLoc,
                                InitialError, DisplayLines, SetResult,
                                ToggleFilters, EventNext, EventPrev,
                                CursorToCurrent)

error_filtered_result_empty = 'filtered result is empty'


def fold_callbacks(cbs, z):
    return cbs.fold_left(Right(z))(lambda z, a: z // L(Try)(a, _))


class ResultAdapter(Record):
    buffer = any_field()
    result = field(ParseResult)
    filters = list_field()
    reifier = either_field(Reifier)
    formatters = list_field()
    syntaxes = list_field()
    initial_error = list_field()

    @lazy
    def vim(self):
        return self.buffer.root

    @property
    def _filters(self):
        return self.filters.cat(DuplicatesFilter(self.vim))

    @lazy
    def filtered(self):
        return fold_callbacks(self._filters, self.result)

    def effective_result(self, filtered: Boolean):
        return self.filtered if filtered else Right(self.result)

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

    @lazy
    def filtered_lines(self):
        return self.filtered // L(Try)(self._reifier, _) // self.format

    @lazy
    def unfiltered_lines(self):
        return Try(self._reifier, self.result) // self.format

    def lines(self, filtered: Boolean):
        return (self.effective_result(filtered) // L(Try)(self._reifier, _) //
                self.format)

    @property
    def langs(self):
        return self.result.langs

    def __repr__(self):
        return repr(self.result)

    def locations(self, filtered: Boolean):
        return self.effective_result(filtered) / _.locations


class OMState(Record):
    result = field(ResultAdapter)
    locations = list_field(Location)
    lines = list_field(OutputLine)
    filter_state = bool_field()
    current_loc_index = dfield(0)


def _jump_first(locs):
    return Empty() if locs.empty else Just(0)


def _jump_last(locs):
    return Empty() if locs.empty else Just(locs.length - 1)


def _jump_default(langs, lang_jumps):
    return langs.find_map(lang_jumps.get) | (lambda: _jump_first)


class OutputMachineTransitions(MyoTransitions):

    @may_handle(SetResult)
    def set_result(self):
        result = self._adapter(self.msg.result)
        return (
            self.with_sub(self.state.set(result=result, filter_state=True)),
            DisplayLines()
        )

    @handle(DisplayLines)
    def display_lines(self):
        return self.set_content.map2(
            lambda a, b: (a, b.replace(Just(InitialError()))))

    @handle(InitialError)
    def initial_error(self):
        jump = self.vim.vars.pb('jump_to_error') | True
        locs = self.locations
        return (
            self.result.initial_error.find_map(__(locs)) /
            L(SetLoc)(_, jump)
        )

    @may_handle(Jump)
    def jump(self):
        open_file = self.open_file(self.msg.target.file_path)
        l, c = self.msg.target.coords
        set_line = Task.delay(lambda: self.vim.window.set_cursor(l, c))
        post = Task.delay(self.vim.cmd, 'normal! zvzz')
        return UnitTask(open_file + set_line + post)

    @handle(JumpCurrent)
    def jump_current(self):
        return self.current_loc / Jump

    @handle(JumpCursor)
    def jump_cursor(self):
        return self.location_for_cursor // self.index_for_location / SetLoc

    @may_handle(ToggleFilters)
    def toggle_filters(self):
        new_state = self.state.filter_state.no
        return (
            self.with_sub(self.state.set(filter_state=new_state)),
            DisplayLines()
        )

    @handle(EventNext)
    def event_next(self):
        return self.cycle_loc(_ < self.state.locations.length, _ + 1)

    @handle(EventPrev)
    def event_prev(self):
        return self.cycle_loc(_ > 0, _ - 1)

    @may_handle(SetLoc)
    def set_loc(self):
        return (
            self.with_sub(self.state.set(current_loc_index=self.msg.index)),
            CursorToCurrent(),
            (JumpCurrent() if self.msg.jump else Nop())
        )

    @handle(CursorToCurrent)
    def cursor_to_current(self):
        cur = self.vim.window
        return (
            self.line_for_current_loc / (
                lambda a:
                Task.delay(self.window.focus) +
                Task.delay(self.window.set_cursor, a + 1) +
                Task.delay(self.window.cmd, 'normal! zz') +
                Task.delay(cur.focus)
            ) /
            UnitTask
        )

    def _adapter(self, result):
        filters = self._callbacks('output_filters')
        reifier = (self._callback('output_reifier')
                   .to_either('no reifier specified'))
        formatters = self._callbacks('output_formatters')
        syntaxes = self._callbacks('output_syntaxes', self.buffer)
        initial_error = (self._callbacks('initial_error',
                                         special=self.special_jumps)
                         .cat(_jump_default(result.langs, self.lang_jumps)))
        return ResultAdapter(buffer=self.buffer, result=result,
                             filters=filters, reifier=reifier,
                             formatters=formatters, syntaxes=syntaxes,
                             initial_error=initial_error)

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
    def special_jumps(self):
        return Map(first=_jump_first, last=_jump_last)

    @property
    def lang_jumps(self):
        return Map(python=_jump_last)

    @property
    def lines(self):
        return self.state.lines

    @property
    def locations(self):
        return self.state.locations

    @property
    def set_content(self):
        min_size = self.vim.vars.pi('output_window_min_size') | 3
        max_size = self.vim.vars.pi('output_window_max_size') | 30
        def run(locations, lines):
            text = lines / _.formatted
            size = min(max_size, max(min_size, text.length))
            return (
                self._with_sub(self.data,
                               self.state.set(locations=locations,
                                              lines=lines)),
                Task.delay(self.window.focus) +
                Task.delay(self.window.cmd, 'resize {}'.format(size)) +
                Task.delay(self.buffer.set_modifiable, True) +
                Task.delay(self.buffer.set_content, text) +
                Task.delay(self.buffer.set_modifiable, False) +
                self.run_syntax(lines)
            )
        def check(locations, lines):
            return (
                Left(Fatal(error_filtered_result_empty))
                if lines.empty else
                Right(run(locations, lines))
            )
        f = self.state.filter_state
        return (self.result.locations(f) &
                self.result.lines(f)).flat_map2(check)

    @property
    def syntax(self):
        lang = self.lang_syntax.to_list
        return self.result.syntaxes.cons(LineGroups(self.vim)) + lang

    @property
    def lang_syntax(self):
        def create(lang):
            return Either.import_name('myo.output.syntax.{}'.format(lang),
                                      'Syntax')
        return self.result.langs.find_map(create) / __(self.vim)

    def run_syntax(self, lines):
        return (self.syntax / (lambda a: a(lines))).sequence(Task)

    def target_for_line(self, line):
        return self.lines.lift(line) / _.target

    def line_for_target(self, target):
        return self.lines.index_where(_.target == target)

    def line_for_location(self, index):
        def same_location(a, b):
            return isinstance(a, Location) and a.same_location(b.target)
        return (
            self.locations.lift(index) //
            (lambda a: self.lines.index_where(L(same_location)(a, _))))

    def index_for_location(self, loc):
        return self.locations.index_where(__.same_location(loc))

    @property
    def location_for_cursor(self):
        return (
            self.vim.window.line /
            (_ - 1) //
            self.target_for_line
        ).filter_type(Location).to_either('not a location')

    @property
    def current_loc(self):
        return self.locations.lift(self.state.current_loc_index)

    @property
    def line_for_current_loc(self):
        return self.line_for_location(self.state.current_loc_index)

    def cycle_loc(self, cond, update):
        cur = self.state.current_loc_index
        return Boolean(cond(cur)).m(update(cur)) / SetLoc

    def open_file(self, path):
        def split():
            # TODO
            pass
        if not path.is_file():
            return Task.now(Left('not a file: {}'.format(path)))
        else:
            win = (
                self.vim.windows.find(__.buffer.modifiable.contains(True))
                .o(split)
                .task('could not get a window') /
                __.focus()
            )
            def load_buffer(buf):
                return Task.delay(self.vim.window.cmd,
                                  'buffer {}'.format(buf.id))
            def edit():
                return Task.delay(self.vim.edit, path) / __.run_async()
            def load_file():
                buf = self.vim.buffers.find(_.name == str(path))
                return buf / load_buffer | edit
            return win + Task.suspend(load_file)


class OutputMachine(ScratchMachine, Logging):
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
    def prefix(self):
        return 'Myo'

    @property
    def mappings(self):
        return Map({
            '%cr%': JumpCursor,
            'f': ToggleFilters,
            'q': Quit,
        })

    def new_state(self):
        return OMState(result=ResultAdapter(buffer=self.scratch.buffer,
                                            result=ParseResult()))

__all__ = ('OutputMachine',)
