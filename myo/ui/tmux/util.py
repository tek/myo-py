import re
from uuid import UUID
from typing import Union

from amino import List, Maybe, Empty, L, _

from ribosome.record import field

from myo.util import parse_id

_session_id_re = re.compile('^\$(\d+)$')


def parse_session_id(value):
    return parse_id(value, _session_id_re, 'session')

_win_id_re = re.compile('^@(\d+)$')


def parse_window_id(value):
    return parse_id(value, _win_id_re, 'window')

_pane_id_re = re.compile('^%(\d+)$')


def parse_pane_id(value):
    return parse_id(value, _pane_id_re, 'pane')


def format_pane(pane):
    return List(pane.desc)


def format_layout(lay):
    return (List(lay.desc) + indent(lay.layouts // format_layout) +
            indent(lay.panes // format_pane))


def indent(lines):
    return lines / '  {}'.format


def format_window(win):
    return List(win.desc) + indent(format_layout(win.root))


def format_state(state) -> List[str]:
    return state.all_windows // format_window

Ident = Union[str, UUID]


def contains_pane_ident(a: Maybe):
    tpes = List(UUID, str)
    bad = lambda a: not tpes.exists(L(isinstance)(a, _))
    err = 'must be Maybe[Ident]'
    return not a.exists(bad), err


def ident_field():
    return field(Maybe, initial=Empty(), invariant=contains_pane_ident)

__all__ = ('parse_window_id', 'parse_pane_id')
