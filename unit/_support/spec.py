from ribosome.test.spec import MockNvimSpec

import myo.test
from myo.test.spec import TmuxSpecBase


class UnitSpec(MockNvimSpec, myo.test.Spec):

    def __init__(self) -> None:
        super().__init__('myo')


class TmuxUnitSpec(UnitSpec, TmuxSpecBase):

    def setup(self) -> None:
        super().setup()
        self._setup_server()

    def teardown(self) -> None:
        super().teardown()
        self._teardown_server()


__all__ = ('UnitSpec', 'TmuxUnitSpec')
