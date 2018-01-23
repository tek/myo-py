import pty
import subprocess
from typing import TypeVar

from kallikrein import k, Expectation

from amino.test.spec import SpecBase
from amino import _, do, Do, __, List, Dat, Map, Lists, Either, L, Try, Regex, Right
from amino.test import fixture_path
from amino.util.numeric import parse_int

from myo.components.tmux.io import TmuxIO, TS
from myo.components.tmux.tmux import Tmux
from myo.tmux.data.pane import Pane
from myo.tmux.data.tmux import TmuxData
from myo.tmux.view_path import ViewPath

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


pane_id_re = Regex('^%(?P<id>\d+)$')


@do(Either[str, int])
def parse_pane_id(pane_id: str) -> Do:
    match = yield pane_id_re.match(pane_id)
    id_s = yield match.group('id')
    yield parse_int(id_s)


class PaneData(Dat['PaneData']):

    @staticmethod
    @do(Either[str, 'PaneData'])
    def from_tmux(pane_id: str) -> Do:
        id = yield parse_pane_id(pane_id)
        yield Right(PaneData(id))

    def __init__(self, id: int) -> None:
        self.id = id


def tmux_fmt_attr(attr: str) -> str:
    return f'#{{{attr}}}'


def tmux_fmt_attrs(attrs: List[str]) -> str:
    raw = (attrs / tmux_fmt_attr).join_tokens
    return f"'{raw}'"


def parse_pane_data(output: List[str]) -> Either[str, List[PaneData]]:
    return output.traverse(lambda kw: Try(PaneData.from_tmux, **kw).join, Either)


def tmux_attr_map(attrs: List[str], output: str) -> Map[str, str]:
    tokens = Lists.split(output, ' ')
    return Map(attrs.zip(tokens))


pane_data_attrs = List(
    'pane_id',
)


@do(TmuxIO[List[Map[str, str]]])
def all_panes_attrs(attrs: List[str]) -> Do:
    output = yield TmuxIO.read('list-panes', '-a', '-F', tmux_fmt_attrs(attrs))
    yield TmuxIO.pure(output / L(tmux_attr_map)(attrs, _))


@do(TmuxIO[List[PaneData]])
def all_panes() -> Do:
    pane_attrs = yield all_panes_attrs(pane_data_attrs)
    yield TmuxIO.from_either(parse_pane_data(pane_attrs))


class IoSpec(SpecBase):
    '''
    test $test
    '''

    def setup(self) -> None:
        self.socket = 'op'
        self.proc = start_tmux(self.socket, True)
        self.tmux = Tmux.cons(self.socket)
        self._wait(1)

    def teardown(self) -> None:
        self.proc.kill()
        self.proc.wait()
        self.tmux.kill_server()

    def test(self) -> Expectation:
        @do(TmuxIO[None])
        def go() -> Do:
            yield TmuxIO.write('new-session')
            # yield TmuxIO.write('new-session')
            # yield TmuxIO.write('new-window')
            # yield TmuxIO.write('split-window')
            # s = yield TmuxIO.read('list-sessions')
            # yield TmuxIO.write('split-window')
            p = yield all_panes()
            # yield TmuxIO.pure((s, p))
            yield TmuxIO.pure(p)
        result = go().result(self.tmux)
        print(result)
        self._wait(1)
        return k(1) == 1

__all__ = ('IoSpec',)
