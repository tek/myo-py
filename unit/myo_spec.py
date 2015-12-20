from pathlib import Path

import sure  # NOQA
from flexmock import flexmock  # NOQA

from myo.main import Myo

from tryp import List, Just, _, Map

from myo.test.spec import MockNvimSpec
from myo.plugins.command import AddVimCommand

class Myo_(MockNvimSpec):

    def cmd(self):
        plugs = List('myo.plugins.command')
        prot = Myo(self.vim, Path('/dev/null'), plugs)
        prot.start()
        prot.send_wait(AddVimCommand('ls', {'name': 'ls', 'vcmd': 'ls'}))
        prot.stop()

__all__ = ['Myo_']
