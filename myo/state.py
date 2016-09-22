from ribosome import Machine, NvimFacade, RootMachine
from ribosome.nvim import HasNvim

from amino import List, _, L, Map
from ribosome.machine.state import SubMachine, SubTransitions

from myo.logging import Logging
from myo.env import Env
from myo.util.callback import parse_callback_spec
from myo.util.callback import VimCallback


class MyoHelpers:

    @property
    def options(self):
        return Map()

    def _callback_errors(self, spec, cb):
        def log(s, e):
            self.log.error('failed to parse callback \'{}\': {}'.format(s, e))
        (spec.zip(cb)).map2(lambda s, c: c.lmap(L(log)(s, _)))

    def _inst_callback(self, name, target):
        t = target or self.vim
        return name(t) if issubclass(name, VimCallback) else name

    def _inst_callbacks(self, spec, target):
        cb = spec / parse_callback_spec / _.join
        self._callback_errors(spec, cb)
        return cb.filter(_.is_right).join / L(self._inst_callback)(_, target)

    def _callback(self, name, target=None):
        spec = self.options.get(name).o(self.vim.vars.p(name))
        return self._inst_callbacks(spec, target)

    def _callbacks(self, name, target=None):
        t = target or self.vim
        def inst(name):
            return name(t) if issubclass(name, VimCallback) else name
        var = self.vim.vars.pl(name) | List()
        opt = self.options.get(name) | List()
        return self._inst_callbacks(var + opt, target)


class MyoComponent(SubMachine, MyoHelpers, HasNvim, Logging):

    def __init__(self, vim: NvimFacade, parent=None, title=None) -> None:
        Machine.__init__(self, parent, title=title)
        HasNvim.__init__(self, vim)


class MyoState(RootMachine, Logging):
    _data_type = Env

    @property
    def title(self):
        return 'myo'


class MyoTransitions(SubTransitions, MyoHelpers, HasNvim, Logging):

    @property
    def options(self):
        return self.msg.options

    def __init__(self, machine, *a, **kw):
        SubTransitions.__init__(self, machine, *a, **kw)
        HasNvim.__init__(self, machine.vim)

__all__ = ('MyoComponent', 'MyoState', 'MyoTransitions')
