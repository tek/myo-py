import subprocess

import libtmux
from libtmux.exc import LibTmuxException

import tryp.test
from tryp.test.path import fixture_path

from myo.ui.tmux.server import Server


class Spec(tryp.test.Spec):
    pass


class TmuxSpec(Spec):

    def setup(self):
        self.win_width = 100
        self.win_height = 40
        super().setup()

    def _find_server(self):
        if self.server is None:
            try:
                self.server = Server(libtmux.Server(socket_name=self.socket))
            except LibTmuxException:
                pass
        return self.server is not None

    def _find_session(self):
        if self.session is None:
            try:
                self.session = self.server.sessions[0]
            except LibTmuxException:
                pass
        return self.session is not None

    def _setup_server(self):
        conf = fixture_path('conf', 'tmux.conf')
        self.socket = 'myo_spec'
        geom = '{}x{}'.format(self.win_width + 1, self.win_height + 1)
        args = ['urxvt', '-geometry', geom, '-e', 'tmux', '-L',
                self.socket, '-f', str(conf)]
        self.term = subprocess.Popen(args, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)
        self.server = None
        self.session = None
        self._wait_for(self._find_server)
        self._wait_for(self._find_session)

    def _teardown_server(self):
        self.term.kill()
        self.server.kill()

    @property
    def sessions(self):
        return self.server.sessions

__all__ = ('Spec', 'TmuxSpec')
