from kallikrein import Expectation
from kallikrein.matchers import contain

from chiasma.commands.pane import capture_pane

from amino.test.spec import SpecBase
from amino import do, Do, List, Map
from amino.test import temp_dir

from ribosome.test.integration.tmux import tmux_plugin_test, screenshot
from ribosome.nvim.api.ui import send_input
from ribosome.nvim.io.compute import NvimIO
from ribosome.util.persist import store_json_data

from myo import myo_config
from myo.data.command import HistoryEntry, Command, SystemInterpreter

from test.tmux import tmux_test_config
from test.klk.tmux import tmux_await_k

cmd1 = Command.cons('cmd1', lines=List('echo cmd1'), interpreter=SystemInterpreter.str('make'))
cmd2 = Command.cons('cmd2', lines=List('echo cmd2'), interpreter=SystemInterpreter.str('make'))
history = List(HistoryEntry.cons(cmd1), HistoryEntry.cons(cmd2))


@do(NvimIO[Expectation])
def history_menu_spec() -> Do:
    yield send_input(':call MyoHistoryMenu()<cr>')
    shot1 = yield screenshot('command', 'history', 'menu', 'menu')
    yield send_input('j')
    yield send_input('<cr>')
    shot2 = yield screenshot('command', 'history', 'menu', 'final')
    cmd_output = yield tmux_await_k(contain('cmd2'), capture_pane, 1)
    return shot1 & shot2 & cmd_output


@do(NvimIO[None])
def pre() -> Do:
    yield store_json_data('history', history)


vars = Map(
    myo_load_history=True,
    ribosome_state_dir=str(temp_dir('command', 'history', 'persist')),
    ribosome_session_name='spec',
)


test_config = tmux_test_config(myo_config, extra_vars=vars).copy(pre=pre)


class HistoryMenuSpec(SpecBase):
    '''
    select history entry from menu $menu
    '''

    def menu(self) -> Expectation:
        return tmux_plugin_test(test_config, history_menu_spec)


__all__ = ('HistoryMenuSpec',)
