import re

from tryp.task import task
from tryp import __, List

from trypnv.record import maybe_field, field

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_id

_id_re = re.compile('^%(\d+)$')


def parse_pane_id(value):
    return parse_id(value, _id_re, 'pane')


class Pane(View):
    id = maybe_field(int)
    name = field(str)

    @property
    def id_s(self):
        return self.id / '%{}'.format


class VimPane(Pane):
    pass


class PaneAdapter(Adapter):

    @property
    def id(self):
        return self.native._pane_id

    @property
    def id_i(self):
        return parse_pane_id(self.id)

    @task
    def resize(self, size, horizontal):
        f = __.set_width if horizontal else __.set_height
        return f(size)(self.native)

    def split(self, horizontal):
        return self.native.split_window(vertical=not horizontal)

    @property
    def size(self):
        return int(self.native.width), int(self.native.height)

    def send_keys(self, cmd, enter=True, suppress_history=True):
        return self.native.send_keys(cmd, enter=enter,
                                     suppress_history=suppress_history)

    @property
    def capture(self):
        return List.wrap(self.native.cmd('capture-pane', '-p').stdout)

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
