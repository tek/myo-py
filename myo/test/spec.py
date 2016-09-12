from subprocess import Popen, PIPE, STDOUT

import libtmux
from libtmux.exc import LibTmuxException

import amino.test
from amino.test.path import fixture_path
from amino import List, _, __
from amino.test import later
from amino.lazy import lazy

from myo.ui.tmux.server import Server


class Spec(amino.test.Spec):
    pass


class TmuxSpecBase(Spec):

    def setup(self):
        self.win_width = 100
        self.win_height = 40
        super().setup()

    @property
    def socket(self):
        return 'myo_spec'

    def _find_server(self):
        if self.native_server is None:
            try:
                self.native_server = libtmux.Server(socket_name=self.socket)
            except LibTmuxException:
                pass
        return self.native_server is not None

    def _find_session(self):
        try:
            return self.session is not None
        except LibTmuxException:
            pass

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
        self.native_server = None
        self.term
        self._wait_for(self._find_server)
        self._wait_for(self._find_session)

    def _teardown_server(self):
        self.term.kill()
        self.server.kill()

    @property
    def server(self):
        return Server(self.native_server)

    @property
    def session(self):
        return self.server.sessions[0]

    @property
    def sessions(self):
        return self.server.sessions

    @property
    def _window(self):
        return self.sessions.head // _.windows.head

    @property
    def _panes(self):
        return self._window / _.panes | List()

    def _pane_with_id(self, id):
        return self._panes.find(__.id_i.contains(id))

    @property
    def _sizes(self):
        return self._panes / _.size

    @property
    def _output(self):
        return self._panes // _.capture

    def _output_contains(self, target):
        later(lambda: self._output.should.contain(target))

__all__ = ('Spec', 'TmuxSpecBase')
