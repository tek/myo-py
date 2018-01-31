from amino import Dat, do, Either, Do, Right, List, Nil, Regex, _, Boolean
from amino.util.numeric import parse_int

from myo.components.tmux.io import TmuxIO
from myo.tmux.command import tmux_data_cmd


session_id_re = Regex('^\$(?P<id>\d+)$')


@do(Either[str, int])
def parse_session_id(session_id: str) -> Do:
    match = yield session_id_re.match(session_id)
    id_s = yield match.group('id')
    yield parse_int(id_s)


class SessionData(Dat['SessionData']):

    @staticmethod
    @do(Either[str, 'SessionData'])
    def from_tmux(session_id: str) -> Do:
        id = yield parse_session_id(session_id)
        yield Right(SessionData(id))

    def __init__(self, id: int) -> None:
        self.id = id


session_data_attrs = List(
    'session_id',
)


def sessions() -> TmuxIO[List[SessionData]]:
    return tmux_data_cmd('list-sessions', Nil, session_data_attrs, SessionData.from_tmux)


@do(TmuxIO[Boolean])
def session_exists(id: str) -> Do:
    ss = yield sessions()
    yield Right(ss.exists(_.id == id))


@do(TmuxIO[None])
def create_session(name: str) -> Do:
    yield TmuxIO.write('new-session', '-s', name)


__all__ = ('sessions', 'session_exists', 'create_session')
