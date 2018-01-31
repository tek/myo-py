from amino import Dat, do, Either, Do, Right, List, Nil, Regex, _, Boolean
from amino.util.numeric import parse_int

from myo.tmux.io.compute import TmuxIO
from myo.tmux.command import tmux_data_cmd
from myo.tmux.commands.session import sessions


window_id_re = Regex('^@(?P<id>\d+)$')


@do(Either[str, int])
def parse_window_id(window_id: str) -> Do:
    match = yield window_id_re.match(window_id)
    id_s = yield match.group('id')
    yield parse_int(id_s)


def window_id(id: int) -> str:
    return f'@{id}'


class WindowData(Dat['WindowData']):

    @staticmethod
    @do(Either[str, 'WindowData'])
    def from_tmux(window_id: str, window_width: str, window_height: str) -> Do:
        id = yield parse_window_id(window_id)
        w = yield parse_int(window_width)
        h = yield parse_int(window_height)
        yield Right(WindowData(id, w, h))

    def __init__(self, id: int, width: int, height: int) -> None:
        self.id = id
        self.width = width
        self.height = height


window_data_attrs = List(
    'window_id',
    'window_width',
    'window_height',
)


def windows() -> TmuxIO[List[WindowData]]:
    return tmux_data_cmd('list-windows', Nil, window_data_attrs, WindowData.from_tmux)


@do(TmuxIO[Either[str, WindowData]])
def window(window_id: int) -> Do:
    ws = yield windows()
    return ws.find(_.id == window_id).to_either(lambda: f'no window with id {window_id}')


@do(TmuxIO[Boolean])
def window_exists(id: str) -> Do:
    ss = yield windows()
    yield Right(ss.exists(_.id == id))


@do(TmuxIO[None])
def create_window(session_id: str, name: str) -> Do:
    yield TmuxIO.write('new-window', '-t', session_id, '-n', name)


@do(TmuxIO[Either[str, List[WindowData]]])
def session_windows(session_id: str) -> Do:
    yield tmux_data_cmd('list-windows', List('-t', session_id), window_data_attrs, WindowData.from_tmux)


@do(TmuxIO[Either[str, WindowData]])
def session_window(session_id: str, window_id: str) -> Do:
    windows = yield session_windows(session_id)
    return windows.find(_.id == window_id).to_either(lambda: f'no window with id {window_id} in session {session_id}')


__all__ = ('windows', 'window_exists', 'create_window', 'session_window', 'window', 'session_windows', 'window_id')
