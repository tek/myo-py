from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists, Path, Nil
from amino.test import fixture_path

from ribosome.test.integration.run import RequestHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.env import Env
from myo.components.command.compute.parse import parse_output
from myo.settings import MyoSettings


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
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
        helper = RequestHelper.strict(config, 'command').update_component('command', commands=List(cmd))
        output = Lists.lines(self.trace_file.read_text())
        result = parse_output(output).run(helper.state).unsafe(None)
        return k(result[1].events).must(have_length(2))


__all__ = ('ParseSpec',)
