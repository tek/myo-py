import re
from numbers import Number

from trypnv.record import maybe_field, field, Record

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_id

_id_re = re.compile('^%(\d+)$')


def parse_pane_id(value):
    return parse_id(value, _id_re, 'pane')


class Measure(Record):
    min_size = maybe_field(int)
    max_size = maybe_field(int)
    fixed_size = maybe_field(int)


class Pane(View):
    id = maybe_field(int)
    name = field(str)
    fixed_size = maybe_field(Number)

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

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
