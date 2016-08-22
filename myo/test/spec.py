import subprocess

import libtmux
from libtmux.exc import LibTmuxException

import amino.test
from amino.test.path import fixture_path
from amino import List, _
from amino.test import later

from myo.ui.tmux.server import Server


class Spec(amino.test.Spec):
    pass


class TmuxSpecBase(Spec):

    def setup(self):
        self.win_width = 100
        self.win_height = 40
        super().setup()

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

    def _setup_server(self):
        conf = fixture_path('conf', 'tmux.conf')
        self.socket = 'myo_spec'
        geom = '{}x{}'.format(self.win_width + 1, self.win_height + 1)
        args = ['urxvt', '-geometry', geom, '-e', 'tmux', '-L',
                self.socket, '-f', str(conf)]
        self.term = subprocess.Popen(args, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        self.native_server = None
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
    def _panes(self):
        return self.sessions.head // _.windows.head / _.panes | List()

    @property
    def _output(self):
        return self._panes // _.capture

    def _output_contains(self, target):
        later(lambda: self._output.should.contain(target))

__all__ = ('Spec', 'TmuxSpecBase')
