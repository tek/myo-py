from libtmux import formats
from libtmux.session import Session as LTSession
from libtmux.common import EnvironmentMixin

from ribosome.record import list_field, maybe_field, field

from amino import List, __, Maybe, Map
from amino.lazy import lazy

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.window import WindowAdapter, Window, NativeWindow
from myo.ui.tmux.util import parse_session_id
from myo.record import Named
from myo.logging import Logging


class Session(Named):
    name = field(str)
    id = maybe_field(int)
    windows = list_field(Window)

    @property
    def desc(self):
        id = self.id / ' {}'.format | ''
        return 'S{}'.format(id)

    @property
    def _str_extra(self):
        return super()._str_extra + self.id.to_list + self.windows


class VimSession(Session):
    session_name = '<vim>'

    def __new__(cls, *a, name=None, **kw):
        n = Maybe(name) | VimSession.session_name
        return super().__new__(cls, *a, name=n, **kw)

    @property
    def desc(self):
        return 'V{}'.format(super().desc)


class NativeSession(LTSession, Logging):

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

    def _list_windows(self):
        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        tmux_formats = ['#{%s}' % format for format in wformats]
        proc = self.cmd('list-windows', '-F%s' % '\t'.join(tmux_formats))
        windows = proc.stdout
        wformats = ['session_name', 'session_id'] + formats.WINDOW_FORMATS
        windows = [dict(zip(
            wformats, window.split('\t'))) for window in windows]
        windows = [
            dict((k, v) for k, v in window.items() if v) for window in windows
        ]
        return windows

    def list_windows(self):
        return [NativeWindow(session=self, **window) for window in
                self._windows]


class SessionAdapter(Adapter):

    @lazy
    def id(self):
        return self.native.id

    @property
    def id_i(self):
        return parse_session_id(self.id)

    @lazy
    def windows(self):
        return List.wrap(self.native.windows) / WindowAdapter

    def window_by_id(self, id):
        return self.windows.find(__.id_i.contains(id))

    def find_pane_by_id(self, id: int):
        return self.windows.find_map(__.pane_by_id(id))

    def new_window(self, **kw):
        return WindowAdapter(self.native.new_window(**kw))

    @property
    def attached(self):
        return int(self.native['session_attached']) > 0

__all__ = ('Session',)
