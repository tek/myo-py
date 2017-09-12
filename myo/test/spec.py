from subprocess import Popen, PIPE, STDOUT
from typing import Union

from libtmux.exc import LibTmuxException

from amino.test.path import fixture_path
from amino import _, __, List, Maybe
from ribosome.test.integration.klk import later

from kallikrein.matchers import contain
from kallikrein import kf, Expectation, k
from amino.lazy import lazy
from amino.test.spec import SpecBase

from myo.ui.tmux.server import Server, NativeServer
from myo.ui.tmux.pane import PaneAdapter
from myo.ui.tmux.window import WindowAdapter
from myo.ui.tmux.session import SessionAdapter


class Spec(SpecBase):
    pass


class TmuxSpecBase(Spec):

    @property
    def win_width(self) -> int:
        return 100

    @property
    def win_height(self) -> int:
        return 40

    @property
    def socket(self) -> str:
        return 'myo_spec'

    @property
    def _socket_name(self) -> Union[str, None]:
        return self.socket if self.external_server else None

    @property
    def native_server(self) -> NativeServer:
        return NativeServer(socket_name=self._socket_name)

    def _find_server(self) -> bool:
        try:
            return self.native_server is not None
        except LibTmuxException:
            return False

    def _find_session(self) -> bool:
        try:
            return self.session is not None
        except LibTmuxException:
            return False

    @property
    def external_server(self) -> bool:
        return True

    @property
    def external_terminal(self) -> bool:
        return True

    @property
    def _terminal_args(self) -> list:
        geom = '{}x{}'.format(self.win_width + 1, self.win_height + 1)
        return ['urxvt', '-geometry', geom, '-e']

    @property
    def _tmux_args(self) -> list:
        conf = fixture_path('conf', 'tmux.conf')
        return ['tmux', '-L', self.socket, '-f', str(conf)]

    @lazy
    def term(self) -> Popen:
        t = self._terminal_args if self.external_terminal else []
        args = t + self._tmux_args
        return Popen(args, stdout=PIPE, stderr=STDOUT)

    def _setup_server(self) -> None:
        if self.external_server:
            self.term
            self._wait_for(self._find_server)
        self._wait_for(self._find_session)

    def _teardown_server(self) -> None:
        if self.external_server:
            self.term.kill()
            self.server.kill()

    @property
    def server(self) -> Server:
        return Server(self.native_server)

    @property
    def sessions(self) -> List[SessionAdapter]:
        return self.server.sessions

    @property
    def session(self) -> SessionAdapter:
        if self.external_server:
            return self.sessions[0]
        else:
            return (self.sessions.find(_.attached)
                    .get_or_fail('no attached session'))

    @property
    def _window(self) -> WindowAdapter:
        return (self.session.windows.last).get_or_fail('no window')

    @property
    def _panes(self) -> List[PaneAdapter]:
        return self._window.panes

    def _pane_with_id(self, id: int) -> Maybe[PaneAdapter]:
        return self._panes.find(__.id_i.contains(id))

    @property
    def _sizes(self) -> List[int]:
        return self._panes / _.size

    @property
    def _output(self) -> List[str]:
        return self._panes // _.capture

    def _output_contains(self, target: str) -> Expectation:
        return later(kf(lambda: self._output).must(contain(target)))

    def _pane_output(self, id: int) -> Maybe[List[str]]:
        return self._pane_with_id(id) / _.capture

    def _pane_output_contains(self, id: int, data: str) -> Expectation:
        def output() -> List[str]:
            return self._pane_output(id) | List()
        return later(kf(output).must(contain(data)))

    def _pane_output_contains_not(self, id: int, data: str) -> Expectation:
        self._wait(1)
        output = self._pane_output(id)
        return k(output).must(contain(~contain(data)))

__all__ = ('Spec', 'TmuxSpecBase')
