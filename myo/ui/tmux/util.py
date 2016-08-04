import re

from myo.util import parse_id

_win_id_re = re.compile('^@(\d+)$')


def parse_window_id(value):
    return parse_id(value, _win_id_re, 'window')

_pane_id_re = re.compile('^%(\d+)$')


def parse_pane_id(value):
    return parse_id(value, _pane_id_re, 'pane')


__all__ = ('parse_window_id', 'parse_pane_id')
