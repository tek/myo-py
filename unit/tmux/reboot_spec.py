from kallikrein import Expectation
from kallikrein.matchers.maybe import be_nothing, be_just
from kallikrein.matchers import contain
from kallikrein.matchers.comparison import eq

from amino import do, Do, List, Lists

from chiasma.data.view_tree import ViewTree
from chiasma.test.tmux_spec import TmuxSpec
from chiasma.commands.pane import capture_pane
from chiasma.io.compute import TmuxIO

from ribosome.nvim.io.state import NS
from ribosome.test.unit import unit_test
from ribosome.test.prog import request

from myo.config.plugin_state import MyoState
from myo.ui.data.view import Layout, Pane
from myo.data.command import Command, SystemInterpreter

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
data = Lists.random_alpha()
cmd = 'comm'

@do(TmuxIO[int])
def marker_count(pane: int) -> Do:
    content = yield capture_pane(pane)
    return len(content.filter(lambda a: a == data))


@do(NS[MyoState, Expectation])
def reboot_spec() -> Do:
    shell = Command.cons(cmd, SystemInterpreter.str('two'), List(f'echo "{data}"'))
    window, space = yield init_tmux_data(layout)
    yield update_command_data(commands=List(shell))
    yield request('open_pane', 'two')
    yield request('run', cmd, '{}')
    yield request('run', cmd, '{}')
    started = yield NS.lift(tmux_await_k(eq(2), marker_count, 1))
    yield request('reboot', cmd)
    rebooted = yield NS.lift(tmux_await_k(eq(1), marker_count, 2))
    return started & rebooted


class RebootSpec(TmuxSpec):
    '''
    kill a command's process running in a tmux pane $reboot
    '''

    def reboot(self) -> Expectation:
        return unit_test(tmux_default_test_config(List('command')), reboot_spec)


__all__ = ('RebootSpec',)
