import abc
from subprocess import Popen, PIPE

import libtmux
import libtmux.formats

from amino import List, Lists, Map, Boolean, do, Either, Do, _, __, Try, Dat, ADT, Nil
from amino.boolean import false, true
from amino.string.hues import blue, red

from myo.tmux.data.session import Session
from myo.tmux.data.window import Window
from myo.tmux.data.pane import Pane

from myo.tmux.native.session import NativeSession
from myo.tmux.native.pane import PaneData, NativePane
from myo.tmux.native.window import NativeWindow
from myo.logging import Logging

libtmux.formats.PANE_FORMATS += [
    'pane_left',
    'pane_top',
]


class NativeServer(libtmux.Server):

    def list_sessions(self):
        return [NativeSession(server=self, **s) for s in self._sessions]

    def list_windows(self):
        return [NativeWindow(server=self, **s) for s in self._windows]


class TmuxCmd(Dat['TmuxCmd']):

    def __init__(self, cmd: str, args: List[str]) -> None:
        self.cmd = cmd
        self.args = args

    @property
    def cmdline(self) -> str:
        return self.args.cons(self.cmd).join_tokens


class TmuxCmdResult(ADT['TmuxCmdResult']):
    pass


class TmuxCmdError(TmuxCmdResult):

    def __init__(self, cmd: TmuxCmd, message: str) -> None:
        self.cmd = cmd
        self.message = message


class TmuxCmdSuccess(TmuxCmdResult):

    def __init__(self, cmd: TmuxCmd, output: List[str]) -> None:
        self.cmd = cmd
        self.output = output


class PState(Dat['PState']):

    def __init__(self, in_cmd: Boolean, current: List[str], cmds: List[List[str]]) -> None:
        self.in_cmd = in_cmd
        self.current = current
        self.cmds = cmds


def parse_cmd_output(output: List[str]) -> List[str]:
    def parse(z: PState, a: str) -> PState:
        return (
            z.set.in_cmd(true)
            if a.startswith('%begin') else
            z.append1.cmds(z.current).set.current(Nil).set.in_cmd(false)
            if a.startswith('%end') else
            z.append1.current(a)
            if z.in_cmd else
            z
        )
    return output.fold_left(PState(false, Nil, Nil))(parse).cmds.drop(1)


def create_cmd_result(cmd: TmuxCmd, output: List[str]) -> TmuxCmdResult:
    return TmuxCmdSuccess(cmd, output)


def create_cmd_results(cmds: List[TmuxCmd], output: List[str]) -> List[TmuxCmdResult]:
    return cmds.zip(parse_cmd_output(output)).map2(create_cmd_result)


class Tmux(Logging, abc.ABC):

    @staticmethod
    def cons(socket: str=None) -> 'Tmux':
        server = NativeServer(socket)
        return NativeTmux(server)

    @abc.abstractproperty
    def sessions(self) -> List[NativeSession]:
        ...

    @abc.abstractmethod
    def session(self, session_id: str) -> Either[str, NativeSession]:
        ...

    @abc.abstractproperty
    def pane_data(self) -> List[PaneData]:
        ...

    def kill_server(self) -> None:
        self.server.kill_server()

    @abc.abstractmethod
    def windows(self, session_id: str) -> Either[str, List[NativeWindow]]:
        ...

    @abc.abstractmethod
    def window(self, session_id: str, window_id: str) -> Either[str, NativeWindow]:
        ...

    @abc.abstractmethod
    def window_exists(self, session_id: str, window_id: str) -> Boolean:
        ...

    @abc.abstractmethod
    def create_window(self, session: Session, window: Window) -> Either[str, NativeWindow]:
        ...

    @abc.abstractmethod
    def control_mode(self, cmds: List[TmuxCmd]) -> List[TmuxCmdResult]:
        ...


class NativeTmux(Tmux):

    def __init__(self, server: libtmux.Server) -> None:
        self.server = server

    def cmd(self, *args: str, **kw: str) -> None:
        ret = self.server.cmd(*args, **kw)
        if ret.stderr:
            self.log.error(f'tmux cmd failed:')
            self.log.error(blue(' '.join(args)))
            Lists.wrap(ret.stderr) / red % self.log.error

    def control_mode(self, cmds: List[TmuxCmd]) -> List[TmuxCmdResult]:
        proc = Popen(args=['tmux', '-L', self.server.socket_name, '-C'], stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     universal_newlines=True)
        cmdlines = (cmds / _.cmdline).cat('').join_lines
        stdout, stderr = proc.communicate(cmdlines)
        output = Lists.lines(stdout)
        return create_cmd_results(cmds, output)

    @property
    def sessions(self) -> List[NativeSession]:
        return Lists.wrap(self.server.list_sessions())

    def session(self, session_id: str) -> Either[str, NativeSession]:
        return self.sessions.find(_.id == session_id).to_either(f'no such session: {session_id}')

    @property
    def pane_data(self):
        return List.wrap(self.server._list_panes()) / Map / PaneData

    def windows(self, session_id: str) -> Either[str, List[NativeWindow]]:
        return self.session(session_id) / __.list_windows()

    @property
    def global_windows(self) -> Either[str, List[NativeWindow]]:
        return self.sessions.traverse(__.list_windows(), Either)

    def window(self, id: str) -> Either[str, NativeWindow]:
        return self.global_windows.find(_.id == id).to_either(f'no window with id `{id}`')

    def session_window(self, session_id: str, window_id: str) -> Either[str, NativeWindow]:
        return self.session(session_id) // __.window(window_id)

    def window_exists(self, session_id: str, window_id: str) -> Boolean:
        return self.session_window(session_id, window_id).replace(true) | false

    @do(Either[str, NativeWindow])
    def create_window(self, session: Session, window: Window) -> Do:
        session_id = yield session.id.to_either('session has no id')
        nsession = yield self.session(session_id)
        yield Try(nsession.create_window, window.name)

    @do(Either[str, NativePane])
    def pane(self, session: Session, window: Window, pane: Pane) -> Do:
        session_id = yield session.id.to_either('session has no id')
        window_id = yield window.id.to_either('window has no id')
        pane_id = yield pane.id.to_either('pane has no id')
        win = yield self.session_window(session_id, window_id)
        yield win.pane(pane_id)

    @do(Either[str, Either[str, NativePane]])
    def create_pane(self, session: Session, window: Window, pane: Pane) -> Do:
        session_id = yield session.id.to_either('session has no id')
        window_id = yield window.id.to_either('window has no id')
        w = yield self.session_window(session_id, window_id)
        yield w.create_pane()

    @property
    def panes(self) -> List[NativePane]:
        return Lists.wrap(NativePane(**pane) for pane in self.server._list_panes())

    def pane_open(self, id: str) -> Boolean:
        return self.pane_data.exists(__.id.contains(id))


class PureTmux(Tmux):

    def __init__(self, _sessions: List[Session], _windows: List[Window], _panes: List[Pane]) -> None:
        self._sessions = _sessions
        self._windows = _windows
        self._panes = _panes

    @property
    def sessions(self) -> List[Session]:
        return self._sessions

__all__ = ('Tmux',)
