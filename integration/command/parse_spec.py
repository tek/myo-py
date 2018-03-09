from typing import Tuple

from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines

from amino import List, Map, Nothing, Path, do, Do, Nil, Just
from amino.test import fixture_path

from ribosome.test.integration.run import DispatchHelper, dispatch_helper
from ribosome.config.config import Config
from ribosome.plugin_state import ComponentDispatch, DispatchAffiliation
from ribosome.dispatch.execute import dispatch_state, run_trans_m
from ribosome.nvim.api import current_buffer_content, current_buffer_name, current_cursor
from ribosome.nvim import NvimIO
from ribosome.test.klk import kn
from ribosome.dispatch.run import DispatchState
from ribosome.dispatch.component import ComponentData

from myo.components.command.config import command
from myo.data.command import Command, HistoryEntry
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.trans.parse import parse
from myo.settings import MyoSettings
from myo.components.command.trans.output import display_parse_result, current_entry_jump
from myo.output.data import ParseResult, CodeEntry, OutputEvent
from myo.output.parser.python import FileEntry, PyErrorEntry, ColEntry

from integration._support.spec import ExternalSpec
from integration._support.python_parse import events


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    component_config_type=MyoComponent,
    settings=MyoSettings(),
)
line, col = 2, 5
file_path = fixture_path('command', 'parse', 'file.py')
entry = FileEntry(
    f'  File "{file_path}", line {line}, in funcname',
    Path(file_path),
    line,
    col,
    Just('funcname'),
    Just(CodeEntry('    yield', 'yield'))
)
output_events = List(
    OutputEvent(
        Nil,
        List(
            entry,
            entry,
            PyErrorEntry('RuntimeError: error', 'error', 'RuntimeError')
        )
    ),
    OutputEvent(
        Nil,
        List(
            entry,
            entry,
            ColEntry('           ^', ' '),
            PyErrorEntry('SyntaxError: error', 'error', 'SyntaxError')
        )
    )
)
parse_result = ParseResult(Nil, output_events, List('python'))


@do(NvimIO[Tuple[DispatchHelper, ComponentData[Env, DispatchAffiliation]]])
def component() -> Do:
    helper = yield dispatch_helper(config, 'command')
    compo = yield NvimIO.from_either(helper.state.component('command'))
    aff = ComponentDispatch(compo)
    compo_data = helper.state.data_for(compo)
    return helper, aff, compo_data


class ParseSpec(ExternalSpec):
    '''
    parse command output $command_output
    jump to current error $jump
    '''

    @property
    def trace_file(self) -> Path:
        return fixture_path('tmux', 'python_parse', 'trace')

    @property
    def component(self) -> Tuple[DispatchHelper, ComponentData[Env, DispatchAffiliation]]:
        helper = DispatchHelper.nvim(config, self.vim, 'command')
        compo = helper.state.component('command').get_or_raise()
        aff = ComponentDispatch(compo)
        return helper, aff

    @property
    def dispatch_state(self) -> DispatchState:
        helper, aff = self.component
        return dispatch_state(helper.state, aff)

    def command_output(self) -> Expectation:
        cmd_ident = 'commo'
        cmd = Command.cons(cmd_ident)
        hist = HistoryEntry(cmd, Nothing)
        helper, aff = self.component
        helper1 = (
            helper
            .update_component('command', commands=List(cmd), history=List(hist), logs=Map({cmd_ident: self.trace_file}))
        )
        @do(NvimIO[List[str]])
        def run() -> Do:
            yield run_trans_m(parse().m).run(dispatch_state(helper1.state, aff))
            yield current_buffer_content()
        return kn(run(), self.vim).must(have_lines(events))

    def jump(self) -> Expectation:
        @do(NvimIO[List[str]])
        def run() -> Do:
            helper, aff, data = yield component()
            (s1, ignore) = yield display_parse_result(parse_result).run(ComponentData(helper.state, data))
            (s2, ignore) = yield current_entry_jump.fun().run(s1)
            name = yield current_buffer_name()
            cursor = yield current_cursor()
            return name, cursor
        return kn(run(), self.vim) == (str(file_path), (line, col))


__all__ = ('ParseSpec',)
