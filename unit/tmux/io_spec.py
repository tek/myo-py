import pty
import subprocess
from typing import TypeVar

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import _, do, Do, __, Just, List
from amino.test import fixture_path

from myo.components.tmux.io import TmuxIO, TS
from myo.components.tmux.tmux import Tmux
from myo.tmux.data.session import Session
from myo.tmux.data.window import Window
from myo.tmux.data.layout import Layout
from myo.tmux.data.pane import Pane
from myo.tmux.data.tmux import TmuxData
from myo.tmux.view_path import ViewPath

win_width = 100
win_height = 40

def terminal_args() -> list:
    geom = '{}x{}'.format(win_width + 1, win_height + 1)
    return ['urxvt', '-geometry', geom, '-e']


def start_tmux(socket: str, term: bool=False) -> subprocess.Popen:
    conf = fixture_path('conf', 'tmux.conf')
    t = terminal_args() if term else []
    args = t + ['tmux', '-L', socket, '-f', str(conf)]
    master, slave = pty.openpty()
    return subprocess.Popen(args, stdout=slave, stdin=slave, stderr=slave)


S = TypeVar('S')


def cmd(name: str, *args: str) -> TS[S, str]:
    return TS.lift(TmuxIO.cmd(name, *args))


@do(TS[TmuxData, None])
def open_pane_path(path: ViewPath[Pane]) -> Do:
    yield cmd('split_window', '-t', path.window.id)


@do(TS[TmuxData, Pane])
def open_pane(name: str) -> Do:
    path = yield TS.inspect_either(__.pane_path(name))
    yield open_pane_path(path)


class IoSpec(SpecBase):
    '''
    test $test
    test2 $test2
    '''

    def test(self) -> Expectation:
        io = TmuxIO.delay(_.sessions)
        return k(1) == 1

    def test2(self) -> Expectation:
        socket = 'myo_spec'
        proc = start_tmux(socket)
        tmux = Tmux.cons(socket)
        session = Session.cons('$0', 's1')
        window = Window.cons('@0', 'w1', session.name)
        layout = Layout.cons(session.name, window.name)
        pane = Pane.cons('p1', session.name, window.name)
        layout1 = layout.add(pane)
        io = open_pane(pane.name)
        data = TmuxData.cons(sessions=List(session), windows=List(window), layouts=List(layout1), panes=List(pane))
        proc.kill()
        proc.wait()
        tmux.kill_server()
        return k(1) == 1


__all__ = ('IoSpec',)
