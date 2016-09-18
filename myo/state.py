from ribosome import Machine, NvimFacade, RootMachine
from ribosome.nvim import HasNvim

from amino import List, Either, _
from ribosome.machine.state import SubMachine, SubTransitions

from myo.logging import Logging
from myo.env import Env
from myo.util import parse_callback_spec


class MyoComponent(SubMachine, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        Machine.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class MyoState(RootMachine, Logging):
    _data_type = Env

    @property
    def title(self):
        return 'myo'


class MyoTransitions(SubTransitions, HasNvim):

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

    def _callbacks(self, name):
        var = self.vim.vars.pl(name) | List()
        opt = self.msg.options.get(name) | List()
        return (
            (var + opt) /
            parse_callback_spec
        ).traverse(_.join, Either)

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
