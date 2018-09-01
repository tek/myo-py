from kallikrein import k, Expectation

from amino.test.spec import SpecBase

from chiasma.util.id import StrIdent
from amino import do, Do, List

from ribosome.test.prog import request_one, request
from ribosome.nvim.io.state import NS
from ribosome.test.integration.external import external_state_test
from ribosome.nvim.io.compute import NvimIO
from ribosome.util.persist import store_json_data
from ribosome.test.config import TestConfig

from myo.config.plugin_state import MyoState
from myo.data.command import Command, HistoryEntry

from test.command import command_spec_config

cmd1 = Command.cons('cmd1')
cmd2 = Command.cons('cmd2')
history = List(HistoryEntry.cons(cmd1, StrIdent('pane1')), HistoryEntry.cons(cmd2))


@do(NS[MyoState, Expectation])
def history_spec() -> Do:
    yield request('init')
    h = yield request_one('history')
    return k(h) == history


@do(NvimIO[None])
def pre() -> Do:
    yield store_json_data('history', history)


test_config = TestConfig.cons(command_spec_config, components=List('core', 'command'), pre=pre)


class HistorySpec(SpecBase):
    '''
    history $history
    '''

    def history(self) -> Expectation:
        return external_state_test(test_config, history_spec)


__all__ = ('HistorySpec',)
