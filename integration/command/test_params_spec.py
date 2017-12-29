from kallikrein import k, Expectation

from amino import Map, List, Right

from myo.components.command.message import StoreTestParams
from myo.command import TestLineParams

from integration._support.command import CmdSpec


class TestParamsSpec(CmdSpec):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        self.send(StoreTestParams(TestLineParams('line', Right('shell'), Right('target'), List('lang'), Map(opt1='val1'))))
        self._wait(1)
        print((self.state_dir / 'test_params.json').read_text())
        return k(1) == 1

__all__ = ('TestParamsSpec',)
