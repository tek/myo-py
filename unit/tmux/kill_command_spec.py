from kallikrein import Expectation
from kallikrein.matchers.maybe import be_nothing, be_just

from amino import do, Do, List

from chiasma.data.view_tree import ViewTree
from chiasma.test.tmux_spec import TmuxSpec

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test
from ribosome.test.prog import request

from myo.config.plugin_state import MyoState
from myo.ui.data.view import Layout, Pane
from myo.data.command import Command, SystemInterpreter
from myo.tmux.pid import process_pid

from test.tmux import tmux_default_test_config, init_tmux_data
from test.klk.tmux import tmux_await_k
from test.command import update_command_data

layout: ViewTree[Layout, Pane] = ViewTree.layout(
    Layout.cons('root', vertical=False),
    List(
        ViewTree.pane(Pane.cons('one', open=True)),
        ViewTree.pane(Pane.cons('two')),
    )
)


@do(NS[MyoState, Expectation])
def kill_command_spec() -> Do:
    shell_cmd = 'python'
    shell = Command.cons(shell_cmd, SystemInterpreter.cons('two'), List(shell_cmd), signals=List('int'))
    window, space = yield init_tmux_data(layout)
    yield update_command_data(commands=List(shell))
    yield request('open_pane', 'two')
    yield request('run_command', shell_cmd, '{}')
    started = yield NS.lift(tmux_await_k(be_just, process_pid, 1))
    yield request('kill', shell_cmd)
    killed = yield NS.lift(tmux_await_k(be_nothing, process_pid, 1))
    return started & killed


class KillCommmandSpec(TmuxSpec):
    '''
    kill a command's process running in a tmux pane $kill
    '''

    def kill(self) -> Expectation:
        return unit_test(tmux_default_test_config(List('command')), kill_command_spec)


__all__ = ('KillCommmandSpec',)
