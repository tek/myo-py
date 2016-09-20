from ribosome import Machine, NvimFacade, RootMachine
from ribosome.nvim import HasNvim

from amino import List, _, L
from ribosome.machine.state import SubMachine, SubTransitions

from myo.logging import Logging
from myo.env import Env
from myo.util import parse_callback_spec
from myo.util.callback import VimCallback


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

    def _callback_errors(self, all, cbs):
        def log(s, e):
            self.log.error('failed to parse callback \'{}\': {}'.format(s, e))
        (all & cbs).map2(lambda s, c: c.lmap(L(log)(s, _)))

    def _callbacks(self, name):
        def inst(name):
            return name() if issubclass(name, VimCallback) else name
        var = self.vim.vars.pl(name) | List()
        opt = self.msg.options.get(name) | List()
        all = var + opt
        cbs = all / parse_callback_spec / _.join
        self._callback_errors(all, cbs)
        return cbs.filter(_.is_right).join / inst

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
