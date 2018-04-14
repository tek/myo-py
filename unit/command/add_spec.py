from kallikrein import Expectation
from kallikrein.matchers import contain

from chiasma.util.id import StrIdent

from amino.test.spec import SpecBase
from amino import List, _, __, do, Do, Nothing, Nil
from amino.json import dump_json

from ribosome.test.integration.run import RequestHelper
from ribosome.nvim.io.compute import NvimIO
from ribosome.test.klk import kn
from ribosome.nvim.io.api import N

from myo.data.command import Command, SystemInterpreter, VimInterpreter, ShellInterpreter
from myo import myo_config


def add_cmd(cmd_type: str, args: dict, goal: Command) -> Expectation[Command]:
    helper = RequestHelper.strict(myo_config, 'command')
    @do(NvimIO[Command])
    def run() -> Do:
        args_json = yield N.e(dump_json(args))
        r = yield helper.run_s(f'command:add_{cmd_type}_command', args=(args_json,))
        yield N.e(r.data_by_name('command') / _.commands // __.head.to_either('commands empty'))
    return kn(helper.vim, run).must(contain(goal))


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
