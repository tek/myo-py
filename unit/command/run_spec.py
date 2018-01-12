from kallikrein import k, Expectation
from kallikrein.matchers.end_with import end_with

from amino.test.spec import SpecBase
from amino import List, Map

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
    run a vim command $vim_cmd
    '''

    def vim_cmd(self) -> Expectation:
        name = 'test'
        cmds = List('let g:key = 7', 'let g:value = 13')
        cmd = Command(name, VimInterpreter(silent=False), cmds)
        helper = DispatchHelper.cons(config, 'command', 'vim').update_data(commands=List(cmd))
        helper.loop('command:run_command', args=(name, '{}')).unsafe(helper.vim)
        return k(helper.vim.vim.request_log).must(end_with(cmds))


__all__ = ('RunSpec',)
