from kallikrein import Expectation

from integration._support.tmux import TmuxCmdSpec

from myo.components.tmux.watcher import Terminated, Stop, Started
from myo.components.tmux.message import WatchCommand


class WatcherSpec(TmuxCmdSpec):
    '''
    test $test
    '''

    def test(self) -> Expectation:
        self._py_shell()
        self.json_cmd_sync('MyoRun py')
        self.seen_message(WatchCommand)
        self.seen_message(Started)
        self.json_cmd_sync('MyoTmuxKill py', signals=['kill'])
        self.seen_message(Terminated)
        return self.seen_message(Stop)

__all__ = ('WatcherSpec',)
