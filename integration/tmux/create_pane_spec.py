from kallikrein import Expectation, k
from kallikrein.matchers.typed import have_type

from amino import do, Do

from chiasma.util.id import StrIdent
from amino.test.spec import SpecBase

from ribosome.nvim.io.compute import NvimIO
from ribosome.nvim.api.command import nvim_command
from ribosome.test.klk.matchers.prog import component_state
from ribosome.test.integration.embed import plugin_test
from ribosome.test.config import TestConfig
from ribosome.nvim.io.api import N

from myo import myo_config
from myo.ui.data.view import Pane


@do(NvimIO[Expectation])
def create_pane_spec() -> Do:
    yield nvim_command('MyoCreatePane', '{ "layout": "make", "ident": "pane"}')
    state = yield component_state('ui')
    space = yield N.m(state.spaces.head, 'no space')
    win = yield N.m(space.windows.head, 'no window')
    layout = yield N.m(win.layout.sub.find(lambda a: a.data.ident == StrIdent('make')), 'no layout `make`')
    pane = yield N.m(layout.sub.find(lambda a: a.data.ident == StrIdent('pane')), 'no pane `pane`')
    return k(pane.data).must(have_type(Pane))


test_config = TestConfig.cons(myo_config)


class CreatePaneSpec(SpecBase):
    '''
    create a pane $create_pane
    '''

    def create_pane(self) -> Expectation:
        return plugin_test(test_config, create_pane_spec)


__all__ = ('CreatePaneSpec',)
