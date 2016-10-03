import libtmux

from ribosome.record import list_field, maybe_field, field

from amino import List, __, Maybe
from amino.lazy import lazy

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.window import WindowAdapter, Window
from myo.ui.tmux.util import parse_session_id
from myo.record import Named


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


class SessionHandler:

    def __init__(self, server: libtmux.Server) -> None:
        self.server = server

    def create_pane(self, pane):
        pass


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
