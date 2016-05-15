import subprocess

import tmuxp
from tmuxp.exc import TmuxpException

import tryp.test


class Spec(tryp.test.Spec):
    pass


class TmuxSpec(Spec):

    def _find_server(self):
        if self.server is None:
            try:
                self.server = tmuxp.Server(socket_name=self.socket)
            except TmuxpException:
                pass
        return self.server is not None

    def _find_session(self):
        if self.session is None:
            try:
                self.session = self.server.sessions[0]
            except TmuxpException:
                pass
        return self.session is not None

    def _setup_server(self):
        self.socket = 'myo_spec'
        args = ['urxvt', '-e', 'tmux', '-L', self.socket, '-f', '/dev/null']
        self.term = subprocess.Popen(args)
        self.server = None
        self.session = None
        self._wait_for(self._find_server)
        self._wait_for(self._find_session)

    def _teardown_server(self):
        self.term.kill()
        self.server.kill_server()

__all__ = ('Spec', 'TmuxSpec')
