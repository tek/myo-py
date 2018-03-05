from kallikrein import Expectation
from kallikrein.matchers.lines import have_lines

from amino import List, Map, Nothing, Path, do, Do
from amino.test import fixture_path

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config
from ribosome.plugin_state import ComponentDispatch
from ribosome.dispatch.execute import dispatch_state, run_trans_m
from ribosome.nvim.api import current_buffer_content
from ribosome.nvim import NvimIO
from ribosome.test.klk import kn

from myo.components.command.config import command
from myo.data.command import Command, HistoryEntry
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.trans.parse import parse
from myo.settings import MyoSettings

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


class ParseSpec(ExternalSpec):
    '''
    parse command output $command_output
    '''

    @property
    def trace_file(self) -> Path:
        return fixture_path('tmux', 'python_parse', 'trace')

    def command_output(self) -> Expectation:
        cmd_ident = 'commo'
        cmd = Command.cons(cmd_ident)
        hist = HistoryEntry(cmd, Nothing)
        helper = (
            DispatchHelper.nvim(config, self.vim, 'command')
            .update_component('command', commands=List(cmd), history=List(hist), logs=Map({cmd_ident: self.trace_file}))
        )
        compo = helper.state.component('command').get_or_raise()
        aff = ComponentDispatch(compo)
        @do(NvimIO[List[str]])
        def run() -> Do:
            yield run_trans_m(parse().m).run(dispatch_state(helper.state, aff))
            yield current_buffer_content()
        return kn(run(), self.vim).must(have_lines(events))


__all__ = ('ParseSpec',)
