from kallikrein import Expectation, k
from kallikrein.matchers.either import be_right

from chiasma.util.id import StrIdent

from amino.test.spec import SpecBase
from amino import List, do, Do, Nothing, Nil
from amino.json import dump_json

from ribosome.test.config import TestConfig
from ribosome.nvim.io.state import NS
from ribosome.test.prog import request
from ribosome.test.unit import unit_test

from myo.data.command import Command, SystemInterpreter, VimInterpreter, ShellInterpreter
from myo import myo_config
from myo.config.plugin_state import MyoState

test_config = TestConfig.cons(myo_config, components=List('command'))


def add_cmd(cmd_type: str, args: dict, goal: Command) -> Expectation[Command]:
    @do(NS[MyoState, Command])
    def run() -> Do:
        args_json = yield NS.e(dump_json(args))
        yield request(f'add_{cmd_type}_command', args_json)
        data = yield NS.inspect_either(lambda s: s.data_by_name('command'))
        cmd = data.commands.head.to_either('commands empty')
        return k(cmd).must(be_right(goal))
    return unit_test(test_config, run)


class AddSpec(SpecBase):
    '''
    add a command
    vim $vim_cmd
    system $system_cmd
    shell $shell_cmd
    '''

    def vim_cmd(self) -> Expectation:
        name = 'lets'
        lines = List('let g:key = 7', 'let g:value = 13')
        args = dict(ident=name, lines=lines)
        goal = Command(StrIdent(name), VimInterpreter.cons(), lines, List('vim'))
        return add_cmd('vim', args, goal)

    def system_cmd(self) -> Expectation:
        name = 'commo'
        lines = List('echo "1"')
        goal = Command(StrIdent(name), SystemInterpreter(Nothing), lines, Nil)
        args = dict(ident=name, lines=lines)
        return add_cmd('system', args, goal)

    def shell_cmd(self) -> Expectation:
        name = 'commo'
        lines = List('print("1")')
        target = 'shello'
        goal = Command(StrIdent(name), ShellInterpreter(StrIdent(target)), lines, Nil)
        args = dict(ident=name, lines=lines, target=target)
        return add_cmd('shell', args, goal)


__all__ = ('AddSpec',)
