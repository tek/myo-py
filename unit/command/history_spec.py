from kallikrein import k, Expectation, pending

from amino.test.spec import SpecBase
from amino import do, Do

from ribosome.test.unit import unit_test
from ribosome.test.prog import request
from ribosome.nvim.io.state import NS
from ribosome.data.plugin_state import PS

from test.command import command_spec_test_config


@do(NS[PS, Expectation])
def history_spec() -> Do:
    yield request('load_history', 5)
    return k(1) == 1


class HistorySpec(SpecBase):
    '''
    history $history
    '''

    @pending
    def history(self) -> Expectation:
        return unit_test(command_spec_test_config, history_spec)


__all__ = ('HistorySpec',)
