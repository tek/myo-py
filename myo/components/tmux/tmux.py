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

    def __init__(self, cmds: List[TmuxCmd], messages: List[str]) -> None:
        self.cmds = cmds
        self.messages = messages


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
        return NativeTmux(socket)

    @abc.abstractmethod
    def execute_cmds(self, cmds: List[TmuxCmd]) -> List[TmuxCmdResult]:
        ...


class NativeTmux(Tmux):

    def __init__(self, socket: str) -> None:
        self.socket = socket

    def execute_cmds(self, cmds: List[TmuxCmd]) -> List[TmuxCmdResult]:
        proc = Popen(args=['tmux', '-L', self.socket, '-C', 'attach'], stdin=PIPE, stdout=PIPE, stderr=PIPE,
                     universal_newlines=True)
        cmdlines = (cmds / _.cmdline).cat('').join_lines
        stdout, stderr = proc.communicate(cmdlines)
        if proc.returncode == 0:
            return create_cmd_results(cmds, Lists.lines(stdout))
        else:
            return List(TmuxCmdError(cmds, Lists.lines(stderr)))


class PureTmux(Tmux):

    def __init__(self, _sessions: List[Session], _windows: List[Window], _panes: List[Pane]) -> None:
        self._sessions = _sessions
        self._windows = _windows
        self._panes = _panes

    def execute_cmds(self, cmds: List[TmuxCmd]) -> List[TmuxCmdResult]:
        return Nil

__all__ = ('Tmux',)
