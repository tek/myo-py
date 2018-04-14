from kallikrein import Expectation, kf, k
from kallikrein.matchers import contain

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import capture_pane
from chiasma.util.id import StrIdent

from amino import List, Lists, Nil

from ribosome.test.integration.klk import later

from myo.data.command import Command, SystemInterpreter, ShellInterpreter
from myo.components.command.data import CommandData

from unit._support.tmux import two_panes


class RunCommandSpec(TmuxSpec):
    '''
    run a command in a tmux pane $run_command
    run a shell in a tmux pane $run_shell
    write output to a file $pipe_pane
    '''

    def run_command(self) -> Expectation:
        name = 'commo'
        text1 = Lists.random_alpha()
        text2 = Lists.random_alpha()
        cmds = List(f'echo {text1}', f'echo {text2}')
        cmd = Command.cons(name, SystemInterpreter.cons('one'), cmds, Nil)
        helper = two_panes(List('command')).update_component('command', commands=List(cmd))
        helper.unsafe_run('command:run_command', args=(name, '{}'))
        output = lambda: capture_pane(0).unsafe(self.tmux)
        return later(kf(output).must(contain(text1) & contain(text2)))

    def run_shell(self) -> Expectation:
        name = 'commo'
        text1 = Lists.random_alpha()
        text2 = Lists.random_alpha()
        shell_cmd = 'python'
        cmds = List(f'print("{text1}")', f'print("{text2}")')
        shell = Command.cons(shell_cmd, SystemInterpreter.cons('one'), List(shell_cmd), Nil)
        cmd = Command.cons(name, ShellInterpreter.cons(shell_cmd), cmds, Nil)
        helper = two_panes(List('command')).update_component('command', commands=List(shell, cmd))
        helper.unsafe_run('command:run_command', args=(shell_cmd, '{}'))
        helper.unsafe_run('command:run_command', args=(name, '{}'))
        output = lambda: capture_pane(0).unsafe(self.tmux)
        return later(kf(output).must(contain(text1) & contain(text2)))

    def pipe_pane(self) -> Expectation:
        name = 'commo'
        text = Lists.random_alpha()
        cmds = List(f'echo {text}')
        cmd = Command.cons(name, SystemInterpreter.cons('one'), cmds, Nil)
        helper = two_panes(List('command')).update_component('command', commands=List(cmd))
        s = helper.unsafe_run_s('command:run_command', args=(name, '{}'))
        path = s.component_data[CommandData].logs[StrIdent('commo')]
        read = lambda: Lists.lines(path.read_text())
        return later(kf(read).must(contain(text)))


__all__ = ('RunCommandSpec',)
