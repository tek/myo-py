import re

from tryp import Maybe, __

from trypnv.record import maybe_field, dfield, field

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_int

_id_re = re.compile('^%(\d+)$')


def parse_id(value):
    return (
        Maybe(_id_re.match(str(value)))
        .map(__.group(1))
        .map(int)
        .to_either("could not match id {}".format(value))
        .or_else(lambda: parse_int(value)))


class Pane(View):
    id = maybe_field(int)
    name = field(str)
    open = dfield(False)

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
        i = self.id[1:]
        return parse_int(i)

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
