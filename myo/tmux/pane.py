import abc

import libtmux

from psutil import Process

from amino import __, List, Maybe, Map, Either, Try, _, Dat
from amino.lazy import lazy

from myo.util import parse_int
from myo.tmux.util import parse_pane_id, parse_window_id, parse_session_id


def child_pids(root: int) -> Either[Exception, List[int]]:
    return (
        Try(Process, root) /
        __.children() /
        List.wrap /
        __.map(_.pid)
    )


def descendant_pids(root: int) -> Either[Exception, List[int]]:
    def recurse(pids: List[int]) -> Either[Exception, List[int]]:
        return pids.traverse(descendant_pids, Either) / _.join / pids.add
    return child_pids(root) // recurse


class PaneI(abc.ABC):

    @abc.abstractproperty
    def _raw_pid(self) -> Maybe[int]:
        ...

    @lazy
    def pid(self) -> Maybe[int]:
        return self._raw_pid // parse_int

    @property
    def command_pid(self) -> Either[Exception, int]:
        return self.pid // child_pids // __.head.to_either('no child pids')

    @property
    def command_pids(self) -> Either[Exception, List[int]]:
        return self.pid // descendant_pids


class PaneData(PaneI, Dat['PaneData']):

    def __init__(self, data: Map[str, str]) -> None:
        self.data = data

    def attr(self, name):
        return (
            self.data.get(name)
            .or_else(self.data.get('pane_{}'.format(name)))
        )

    @lazy
    def id(self):
        return self.attr('id')

    @property
    def id_i(self):
        return self.id // parse_pane_id

    @lazy
    def window_id(self):
        return self.attr('window_id')

    @property
    def window_id_i(self):
        return self.window_id // parse_window_id

    @lazy
    def session_id(self):
        return self.attr('session_id')

    @property
    def session_id_i(self):
        return self.session_id // parse_session_id

    @property
    def _raw_pid(self):
        return self.data.get('pane_pid')


class NativePane(libtmux.Pane):

    def __init__(self, window=None, **kwargs):
        if not window:
            raise ValueError('Pane must have ``Window`` object')
        self.window = window
        self.session = self.window.session
        self.server = self.session.server
        self._pane_id = kwargs['pane_id']
        self._data = Map(kwargs)

    @property
    def _info(self):
        return self._data


__all__ = ('PaneData', 'NativePane')
