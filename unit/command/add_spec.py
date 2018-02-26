from kallikrein import k, Expectation
from kallikrein.matchers.either import be_right

from amino.test.spec import SpecBase
from amino import List, Map, _, __
from amino.json import dump_json

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo.env import Env


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command),
    default_components=List('command'),
)


class AddSpec(SpecBase):
    '''
    add a command $add
    '''

    def add(self) -> Expectation:
        helper = DispatchHelper.cons(config, 'command')
        name = 'cmd_tail'
        params = dump_json(dict(lines=List('let g:key = 7', 'let g:value = 13'))).get_or_raise()
        r = helper.loop('command:add_vim_command', args=(name, params)).unsafe(helper.vim)
        cmd_name = r.data_by_name('command') / _.commands // _.head / _.ident
        return k(cmd_name.to_either('commands empty')).must(be_right(name))


__all__ = ('AddSpec',)
