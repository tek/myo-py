from kallikrein import k, Expectation
from kallikrein.matchers.end_with import end_with

from chiasma.test.tmux_spec import TmuxSpec

from amino.test.spec import SpecBase
from amino import List, Map, Nothing

from ribosome.test.integration.run import DispatchHelper
from ribosome.config.config import Config

from myo.components.command.config import command
from myo import Env, MyoComponent
from myo.data.command import Command, SystemInterpreter
from myo.components.tmux.config import tmux


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command, tmux=tmux),
    component_config_type=MyoComponent,
)


class RunSpec(TmuxSpec):
    '''
    run a tmux command $tmux_cmd
    '''

    def tmux_cmd(self) -> Expectation:
        name = 'test'
        cmds = List('echo 1', 'echo 2')
        cmd = Command(name, SystemInterpreter(Nothing), cmds)
        helper = DispatchHelper.cons(config, 'command', 'tmux').update_data(commands=List(cmd))
        r = helper.loop('command:run_command', args=(name, '{}')).unsafe(helper.vim)
        return k(1) == 1


__all__ = ('RunSpec',)
