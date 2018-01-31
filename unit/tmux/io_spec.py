import pty
import subprocess

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import do, Do
from amino.test import fixture_path

from myo.components.tmux.io import TmuxIO
from myo.components.tmux.tmux import Tmux
from myo.tmux.commands.pane import all_panes, window_panes
from myo.tmux.commands.session import sessions
from myo.tmux.commands.server import kill_server

win_width = 300
win_height = 120


def terminal_args() -> list:
    geom = '{}x{}'.format(win_width + 1, win_height + 1)
    return ['urxvt', '-geometry', geom, '-e']


def start_tmux(socket: str, term: bool=False) -> subprocess.Popen:
    conf = fixture_path('conf', 'tmux.conf')
    t = terminal_args() if term else []
    args = t + ['tmux', '-L', socket, '-f', str(conf)]
    master, slave = pty.openpty()
    return subprocess.Popen(args, stdout=slave, stdin=slave, stderr=slave)


class IoSpec(SpecBase):
    '''
    test $test
    '''

    def setup(self) -> None:
        self.socket = 'op'
        self.proc = start_tmux(self.socket, False)
        self.tmux = Tmux.cons(self.socket)
        self._wait(1)

    def teardown(self) -> None:
        self.proc.kill()
        self.proc.wait()
        kill_server().result(self.tmux)

    def test(self) -> Expectation:
        @do(TmuxIO[None])
        def go() -> Do:
            yield TmuxIO.write('new-session')
            yield TmuxIO.write('new-session')
            yield TmuxIO.write('new-window')
            yield TmuxIO.write('split-window')
            s = yield TmuxIO.read('list-sessions')
            yield TmuxIO.write('split-window')
            p = yield all_panes()
            wp = yield window_panes(3)
            yield TmuxIO.pure((s, wp, p))
        result = go().result(self.tmux)
        self._wait(1)
        return k(1) == 1


__all__ = ('IoSpec',)
