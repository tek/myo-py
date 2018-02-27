from kallikrein import Expectation, kf, k
from kallikrein.matchers.length import have_length
from kallikrein.matchers import contain

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.io.compute import TmuxIO
from chiasma.commands.pane import capture_pane

from amino import List, __, Lists, Just
from amino.boolean import true, false

from ribosome.test.integration.klk import later

from myo.data.command import Command, SystemInterpreter, ShellInterpreter

from unit._support.tmux import two_panes


class RunCommandSpec(TmuxSpec):
    '''
    run a command in a tmux pane $run_command
    run a shell in a tmux pane $run_shell
    '''

    def run_command(self) -> Expectation:
        name = 'commo'
        text1 = Lists.random_alpha()
        text2 = Lists.random_alpha()
        cmds = List(f'echo {text1}', f'echo {text2}')
        cmd = Command(name, SystemInterpreter(Just('one')), cmds)
        helper = two_panes(List('command')).update_component('command', commands=List(cmd))
        helper.loop('command:run_command', args=(name, '{}')).unsafe(helper.vim)
        output = lambda: capture_pane(0).unsafe(self.tmux)
        return later(kf(output).must(contain(text1) & contain(text2)))

    def run_shell(self) -> Expectation:
        name = 'commo'
        text1 = Lists.random_alpha()
        text2 = Lists.random_alpha()
        shell_cmd = 'python'
        cmds = List(f'print("{text1}")', f'print("{text2}")')
        shell = Command(shell_cmd, SystemInterpreter(Just('one')), List(shell_cmd), true)
        cmd = Command(name, ShellInterpreter(shell_cmd), cmds, false)
        helper = two_panes(List('command')).update_component('command', commands=List(shell, cmd))
        helper.loop('command:run_command', args=(shell_cmd, '{}')).unsafe(helper.vim)
        helper.loop('command:run_command', args=(name, '{}')).unsafe(helper.vim)
        output = lambda: capture_pane(0).unsafe(self.tmux)
        return later(kf(output).must(contain(text1) & contain(text2)))


__all__ = ('RunCommandSpec',)
