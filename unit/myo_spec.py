from myo.main import Myo

from tryp import List, Map

from myo.plugins.command import AddShellCommand, Run
from myo.plugins.core.main import StageI

from unit._support.spec import UnitSpec


class Myo_(UnitSpec):

    def cmd(self):
        plugs = List('myo.plugins.command', 'myo.plugins.tmux')
        myo = Myo(self.vim, plugins=plugs)
        with myo.transient():
            myo.send_sync(StageI())
            myo.send_sync(AddShellCommand('ls', Map(line='ls')))
            myo.send_sync(Run('ls', Map()))

__all__ = ('Myo_',)
