from kallikrein import k, Expectation
from kallikrein.matchers.length import have_length

from amino.test.spec import SpecBase
from amino import List, Map, Nothing, Lists

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config
from ribosome.plugin_state import ComponentDispatch
from ribosome.dispatch.execute import dispatch_state, run_trans_m

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.command.trans.parse import parse


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    component_config_type=MyoComponent,
)

_errmsg = 'error 23'

trace = '''Traceback (most recent call last):
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23, in funcname
    yield
RuntimeError: {err}

Cause:
  File "/path/to/file", line 23, in funcname
    yield
  File "/path/to/file", line 23
    wrong =
           ^
SyntaxError: {err}

trailing garbage
'''.format(err=_errmsg)


class ParseSpec(SpecBase):
    '''
    parse command output $parse
    '''

    def parse(self) -> Expectation:
        name = 'test'
        cmds = List('let g:key = 7', 'let g:value = 13')
        cmd = Command(name, VimInterpreter(silent=False, target=Nothing), cmds)
        helper = DispatchHelper.cons(config, 'command').update_component('command', commands=List(cmd))
        compo = helper.state.component('command').get_or_raise()
        output = Lists.lines(trace)
        aff = ComponentDispatch(compo)
        result = run_trans_m(parse(output).m).run(dispatch_state(helper.state, aff)).unsafe(None)
        return k(result[1].events).must(have_length(2))


__all__ = ('ParseSpec',)
