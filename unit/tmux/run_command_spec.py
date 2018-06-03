from kallikrein import Expectation, k
from kallikrein.matchers import contain
from kallikrein.matchers.comparison import eq

from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import capture_pane
from chiasma.util.id import StrIdent
from chiasma.io.compute import TmuxIO

from amino import List, Lists, Nil, do, Do, IO

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test
from ribosome.test.prog import request
from ribosome.test.klk.expectation import await_k
from ribosome.nvim.io.api import N

from myo.data.command import Command, SystemInterpreter, ShellInterpreter
from myo.components.command.data import CommandData
from myo.config.plugin_state import MyoState

from test.command import update_command_data
from test.klk.tmux import tmux_await_k

from test.tmux import two_panes, tmux_default_test_config

name = 'commo'
text1 = Lists.random_alpha()
text2 = Lists.random_alpha()
python_shell_cmd = 'python'
conf = tmux_default_test_config(List('command'))


@do(NS[MyoState, Expectation])
def run_command_spec() -> Do:
    cmds = List(f'echo {text1}', f'echo {text2}')
    cmd = Command.cons(name, SystemInterpreter.cons('one'), cmds, Nil)
    yield two_panes()
    yield update_command_data(commands=List(cmd))
    yield request('run', name, '{}')
    yield NS.lift(tmux_await_k(contain(text1) & contain(text2), capture_pane, 0))


@do(TmuxIO[int])
def text2_count() -> Do:
    content = yield capture_pane(0)
    return len(content.filter(lambda a: a == text2))


@do(NS[MyoState, None])
def python_shell() -> Do:
    cmds = List(f'print("{text1}")', f'print("{text2}")')
    shell = Command.cons(python_shell_cmd, SystemInterpreter.cons('one'), List(python_shell_cmd), Nil)
    cmd = Command.cons(name, ShellInterpreter.cons(python_shell_cmd), cmds, Nil)
    yield two_panes()
    yield update_command_data(commands=List(shell, cmd))


@do(NS[MyoState, Expectation])
def run_shell_spec() -> Do:
    yield python_shell()
    yield request('run', python_shell_cmd, '{}')
    yield request('run', name, '{}')
    yield NS.lift(tmux_await_k(contain(text1) & contain(text2), capture_pane, 0))
    yield request('run', name, '{}')
    yield NS.lift(tmux_await_k(eq(2), text2_count))
    yield NS.lift(tmux_await_k(~contain(f'>>> python'), capture_pane, 0))


@do(NS[MyoState, Expectation])
def pipe_pane_spec() -> Do:
    cmds = List(f'echo {text1}')
    cmd = Command.cons(name, SystemInterpreter.cons('one'), cmds, Nil)
    yield two_panes()
    yield update_command_data(commands=List(cmd))
    yield request('run', name, '{}')
    path = yield NS.inspect(lambda a: a.component_data[CommandData].logs[StrIdent('commo')])
    read = lambda: N.from_io(IO.delay(path.read_text)).map(lambda a: k(Lists.lines(a)).must(contain(text1)))
    yield NS.lift(await_k(read))


@do(NS[MyoState, Expectation])
def rerun_spec() -> Do:
    yield python_shell()
    yield request('run', python_shell_cmd, '{}')
    yield request('run', name, '{}')
    yield NS.lift(tmux_await_k(contain(text1) & contain(text2), capture_pane, 0))
    yield request('rerun')
    yield NS.lift(tmux_await_k(eq(2), text2_count))


class RunCommandSpec(TmuxSpec):
    '''
    run a command in a tmux pane $run_command
    run a shell in a tmux pane $run_shell
    write output to a file $pipe_pane
    run a command from the history $rerun
    '''

    def run_command(self) -> Expectation:
        return unit_test(conf, run_command_spec)

    def run_shell(self) -> Expectation:
        return unit_test(conf, run_shell_spec)

    def pipe_pane(self) -> Expectation:
        return unit_test(conf, pipe_pane_spec)

    def rerun(self) -> Expectation:
        return unit_test(conf, rerun_spec)


__all__ = ('RunCommandSpec',)
