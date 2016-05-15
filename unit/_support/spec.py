from trypnv.test.spec import MockNvimSpec

import myo.test


class UnitSpec(MockNvimSpec, myo.test.Spec):

    def __init__(self):
        super().__init__('myo')

    def setup(self):
        super().setup()





__all__ = ['Spec']
