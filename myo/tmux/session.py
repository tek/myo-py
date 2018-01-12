import libtmux
from libtmux import formats
from libtmux.common import EnvironmentMixin

from amino import Map, _, Either, List, Lists, L, Try

from myo.tmux.window import NativeWindow


class NativeSession(libtmux.Session):

    def __init__(self, server=None, **kwargs):
        EnvironmentMixin.__init__(self)
        self.server = server
        if 'session_id' not in kwargs:
            raise ValueError('Session requires a `session_id`')
        self._session_id = kwargs['session_id']
        self._data = Map(kwargs) + ('id', self._session_id)

    @property
    def _info(self):
        return self._data

    def _list_windows(self) -> List[dict]:
        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in wformats]
        proc = self.cmd('list-windows', '-F%s' % '\t'.join(tmux_formats))
        windows = proc.stdout
        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        windows = [dict(zip(
            wformats, window.split('\t'))) for window in windows]
        return Lists.wrap([
            dict((k, v) for k, v in window.items() if v) for window in windows
        ])

    def list_windows(self) -> List[NativeWindow]:
        return self._list_windows() / (lambda w: NativeWindow(session=self, **w))

    def window(self, window_id: str) -> Either[str, NativeWindow]:
        return self.list_windows().find(_.id == window_id).to_either(f'no such window: {window_id}')

    def create_window(self, name: str) -> Either[str, NativeWindow]:
        return Try(self.new_window, window_name=name)


__all__ = ('NativeSession',)
