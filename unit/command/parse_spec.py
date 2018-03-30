from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists, Path, Nil
from amino.test import fixture_path

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config
from ribosome.plugin_state import ComponentDispatch
from ribosome.dispatch.execute import DispatchState

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.trans.parse import parse_output
from myo.settings import MyoSettings


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    component_config_type=MyoComponent,
    settings=MyoSettings(),
)


class ParseSpec(SpecBase):
    '''
    parse text $text
    '''

    @property
    def trace_file(self) -> Path:
        return fixture_path('tmux', 'parse', 'trace')

    def text(self) -> Expectation:
        name = 'test'
        cmds = List('let g:key = 7', 'let g:value = 13')
        cmd = Command(name, VimInterpreter(silent=False, target=Nothing), cmds, Nil)
        helper = DispatchHelper.strict(config, 'command').update_component('command', commands=List(cmd))
        compo = helper.state.component('command').get_or_raise()
        output = Lists.lines(self.trace_file.read_text())
        aff = ComponentDispatch(compo)
        result = parse_output(output).run(DispatchState(helper.state, aff)).unsafe(None)
        return k(result[1].events).must(have_length(2))


__all__ = ('ParseSpec',)
