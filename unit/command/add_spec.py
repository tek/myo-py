from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, Map
from amino.json import dump_json

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo import Env


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    core_components=List(),
    default_components=List('command'),
)


class AddSpec(SpecBase):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        helper = DispatchHelper.cons(config, 'command')
        name = 'cmd_tail'
        params = dump_json(dict(line='tail', target='main')).get_or_raise()
        r = helper.loop('command:add_system_command', args=(name, params)).unsafe(helper.vim)
        print(r.data)
        return k(1) == 1


__all__ = ('AddSpec',)
