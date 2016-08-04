from tryp.task import task
from tryp import __, List
from tryp.lazy import lazy

from trypnv.record import maybe_field, field

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_int
from myo.ui.tmux.util import parse_window_id, parse_pane_id


class Pane(View):
    id = maybe_field(int)
    pid = maybe_field(int)
    name = field(str)

    @property
    def id_s(self):
        return self.id / '%{}'.format

    @property
    def desc(self):
        id = self.id / ' %{}'.format | ''
        pid = self.pid / ' | pid -> {}'.format | ''
        return 'P{} \'{}\'{} {}'.format(id, self.name, pid, self.size_desc)


class VimPane(Pane):

    @property
    def desc(self):
        return 'V{}'.format(super().desc)


class PaneAdapter(Adapter):

    @lazy
    def id(self):
        return self.native.id

    @lazy
    def id_i(self):
        return parse_pane_id(self.id)

    @lazy
    def pid(self):
        return parse_int(self.native.pid)

    @task
    def resize(self, size, horizontal):
        f = __.set_width if horizontal else __.set_height
        return f(size)(self.native)

    @property  # type: ignore
    @task
    def kill(self):
        return self.native.cmd('kill-pane')

    def split(self, horizontal):
        return self.native.split_window(vertical=not horizontal)

    @lazy
    def size(self):
        return int(self.native.width), int(self.native.height)

    def send_keys(self, cmd, enter=True, suppress_history=True):
        return self.native.send_keys(cmd, enter=enter,
                                     suppress_history=suppress_history)

    @property
    def capture(self):
        return List.wrap(self.native.cmd('capture-pane', '-p').stdout)

    @lazy
    def window_id(self):
        return self.native.window.id

    @lazy
    def window_id_i(self):
        return parse_window_id(self.window_id)

    def __repr__(self):
        return 'PA({})'.format(self.id, self.size)

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
