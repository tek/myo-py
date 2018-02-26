from kallikrein import k, Expectation
from kallikrein.matchers.end_with import end_with

from amino.test.spec import SpecBase
from amino import List, Map, Nothing

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.components.vim.config import vim
from myo.env import Env
from myo.config.component import MyoComponent
from myo.components.ui.config import ui


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command, vim=vim, ui=ui),
    component_config_type=MyoComponent,
)


class RunSpec(SpecBase):
    '''
    run a vim command $vim_cmd
    '''

    def vim_cmd(self) -> Expectation:
        name = 'test'
        cmds = List('let g:key = 7', 'let g:value = 13')
        cmd = Command(name, VimInterpreter(silent=False, target=Nothing), cmds)
        helper = DispatchHelper.cons(config, 'command', 'vim', 'ui').update_component('command', commands=List(cmd))
        helper.loop('command:run_command', args=(name, '{}')).unsafe(helper.vim)
        return k(helper.vim.vim.request_log).must(end_with(cmds))


__all__ = ('RunSpec',)
