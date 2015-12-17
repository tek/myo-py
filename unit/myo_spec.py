from pathlib import Path

import sure  # NOQA
from flexmock import flexmock  # NOQA

from myo.main import Myo

from tryp import List, Just, _, Map

from unit._support.spec import MockNvimSpec

class Myo_(MockNvimSpec):

    def test(self):
        prot = Myo(self.vim, Path('/dev/null'), List())

__all__ = ['Myo_']
