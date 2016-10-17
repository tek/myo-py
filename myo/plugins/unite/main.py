from ribosome.machine import may_handle
from ribosome.unite import UniteMessage, UniteSource, UniteKind

from amino import Map, List

from myo.plugins.unite.message import UniteHistory
from myo.state import MyoTransitions, MyoComponent


class UniteTransitions(MyoTransitions):

    def unite_cmd(self, cmd):
        args = ' '.join(self.msg.unite_args)
        self.vim.cmd('Unite {} {}'.format(cmd, args))

    @may_handle(UniteHistory)
    def history(self):
        self.unite_cmd(UniteNames.history)


class Plugin(MyoComponent):
    Transitions = UniteTransitions

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._unite_ready = False

    def prepare(self, msg):
        if not self._unite_ready and isinstance(msg, UniteMessage):
            self._setup_unite()

    def _setup_unite(self):
        history = UniteSource(UniteNames.history,
                              UniteNames.history_candidates,
                              UniteNames.history)
        run_action = Map(name='run', handler=UniteNames.run,
                         desc='run command')
        run = UniteKind(UniteNames.history, List(run_action))
        history.define(self.vim)
        run.define(self.vim)
        self._unite_ready = True


class UniteNames():
    history_candidates = '_myo_unite_history'

    run = '_myo_unite_run_project'

    history = 'myo_history'

__all__ = ('Plugin', 'UniteNames')
