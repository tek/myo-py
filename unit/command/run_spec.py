from kallikrein import k, Expectation
from kallikrein.matchers.end_with import end_with

from amino.test.spec import SpecBase
from amino import List, Map, Nil, do, Do

from ribosome.config.config import Config
from ribosome.test.config import TestConfig
from ribosome.test.unit import unit_test
from ribosome.test.prog import request
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS
from ribosome.nvim.api.rpc import nvim_api

from myo.components.command.config import command
from myo.data.command import Command, VimInterpreter
from myo.components.vim.config import vim
from myo.env import Env
from myo.components.ui.config import ui

from test.command import update_command_data


config = Config.cons(
    name='myo',
    prefix='myo',
    state_ctor=Env.cons,
    components=Map(command=command, vim=vim, ui=ui),
)
test_config = TestConfig.cons(config, components=List('command', 'vim', 'ui'))


@do(NS[PS, Expectation])
def vim_cmd_spec() -> Do:
    name = 'test'
    cmds = List('let g:key = 7', 'let g:value = 13')
    cmd = Command.cons(name, VimInterpreter.cons(), cmds, Nil)
    yield update_command_data(commands=List(cmd))
    yield request('run_command', name, '{}')
    vim = yield NS.lift(nvim_api())
    return k(vim.request_log.flat_map(lambda a: a[1].head)).must(end_with(cmds))


class RunSpec(SpecBase):
    '''
    run a vim command $vim_cmd
    '''

    def vim_cmd(self) -> Expectation:
        return unit_test(test_config, vim_cmd_spec)


__all__ = ('RunSpec',)
