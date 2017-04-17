from subprocess import Popen, PIPE, STDOUT

from libtmux.exc import LibTmuxException

from amino.test.path import fixture_path
from amino import _, __, List
from ribosome.test.integration.klk import later

from kallikrein.matchers import contain
from kallikrein import kf
from amino.lazy import lazy
from amino.test.spec import SpecBase

from myo.ui.tmux.server import Server, NativeServer


class Spec(SpecBase):
    pass


class TmuxSpecBase(Spec):

    @property
    def win_width(self):
        return 100

    @property
    def win_height(self):
        return 40

    @property
    def socket(self):
        return 'myo_spec'

    @property
    def _socket_name(self):
        return self.socket if self.external_server else None

    @property
    def native_server(self):
        return NativeServer(socket_name=self._socket_name)

    def _find_server(self):
        try:
            return self.native_server is not None
        except LibTmuxException:
            pass

    def _find_session(self):
        try:
            return self.session is not None
        except LibTmuxException:
            pass

    @property
    def external_server(self):
        return True

    @property
    def external_terminal(self):
        return True

    @property
    def _terminal_args(self):
        geom = '{}x{}'.format(self.win_width + 1, self.win_height + 1)
        return ['urxvt', '-geometry', geom, '-e']

    @property
    def _tmux_args(self):
        conf = fixture_path('conf', 'tmux.conf')
        return ['tmux', '-L', self.socket, '-f', str(conf)]

    @lazy
    def term(self):
        t = self._terminal_args if self.external_terminal else []
        args = t + self._tmux_args
        return Popen(args, stdout=PIPE, stderr=STDOUT)

    def _setup_server(self):
        if self.external_server:
            self.term
            self._wait_for(self._find_server)
        self._wait_for(self._find_session)

    def _teardown_server(self):
        if self.external_server:
            self.term.kill()
            self.server.kill()

    @property
    def server(self):
        return Server(self.native_server)

    @property
    def sessions(self):
        return self.server.sessions

    @property
    def session(self):
        if self.external_server:
            return self.sessions[0]
        else:
            return (self.sessions.find(_.attached)
                    .get_or_fail('no attached session'))

    @property
    def _window(self):
        return (self.session.windows.last).get_or_fail('no window')

    @property
    def _panes(self):
        return self._window.panes

    def _pane_with_id(self, id):
        return self._panes.find(__.id_i.contains(id))

    @property
    def _sizes(self):
        return self._panes / _.size

    @property
    def _output(self):
        return self._panes // _.capture

    def _output_contains(self, target):
        return later(kf(lambda: self._output).must(contain(target)))

    def _pane_output(self, id):
        return self._pane_with_id(id) / _.capture

    def _pane_output_contains(self, id, data):
        def check():
            output = self._pane_output(id) | List()
            output.should.contain(data)
        later(check)

    def _pane_output_contains_not(self, id, data):
        self._wait(1)
        def check():
            output = self._pane_output(id) | List()
            output.should_not.contain(data)
        later(check)

__all__ = ('Spec', 'TmuxSpecBase')
