from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import List, Map
from amino.json import dump_json

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo import Env, MyoComponent
from myo.data.command import Command, VimInterpreter
from myo.components.vim.config import vim


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command, vim=vim),
    component_config_type=MyoComponent,
)


class RunSpec(SpecBase):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        name = 'test'
        cmds = List('let g:key = 7', 'let g:value = 13')
        cmd = Command(name, VimInterpreter, cmds)
        helper = DispatchHelper.cons(config, 'command', 'vim').update_data(commands=List(cmd))
        params = dump_json(dict()).get_or_raise()
        helper.loop('command:run_command', args=(name, params)).unsafe(helper.vim)
        return k(helper.vim.vim.request_log[-2:]) == cmds.map(lambda a: f'silent {a}')


__all__ = ('RunSpec',)
