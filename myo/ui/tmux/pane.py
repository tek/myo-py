import abc
from pathlib import Path
import tempfile
import os

from amino.task import task

from psutil import Process
from amino import __, List, Boolean, Maybe, _, Map, Just
from amino.lazy import lazy

from ribosome.record import maybe_field, either_field

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_int
from myo.ui.tmux.util import parse_window_id, parse_pane_id, parse_session_id


class Pane(View):
    id = maybe_field(int)
    pid = maybe_field(int)
    shell_pid = maybe_field(int)
    window_id = either_field(int)
    session_id = either_field(int)
    log_path = maybe_field(Path)

    @property
    def id_s(self):
        return self.id / '%{}'.format

    @property
    def desc(self):
        id = self.id / ' %{}'.format | ''
        pid = self.pid / ' | pid -> {}'.format | ''
        return 'P{} \'{}\'{} {}'.format(id, self.name, pid, self.size_desc)

    def open(self, pa: 'PaneAdapter'):
        return self.set(id=pa.id_i.to_maybe, shell_pid=pa.pid.to_maybe,
                        session_id=pa.session_id_i, window_id=pa.window_id_i)


class VimPane(Pane):

    @property
    def desc(self):
        return 'V{}'.format(super().desc)


class PaneI(metaclass=abc.ABCMeta):

    @abc.abstractproperty
    def _raw_pid(self) -> Maybe[int]:
        ...

    @lazy
    def pid(self):
        return self._raw_pid // parse_int

    @lazy
    def command_pid(self) -> Maybe[int]:
        return (
            self.pid /
            Process /
            __.children() /
            List.wrap //
            _.head /
            _.pid //
            Maybe
        )


class PaneData(PaneI):

    def __init__(self, data: Map) -> None:
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


class PaneAdapter(Adapter, PaneI):

    @lazy
    def id(self):
        return self.native.id

    @lazy
    def id_i(self):
        return parse_pane_id(self.id)

    @property
    def _raw_pid(self):
        return Just(self.native.pid)

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

    @property
    def session_id(self):
        return self.native.session.id

    @lazy
    def session_id_i(self):
        return parse_session_id(self.session_id)

    @lazy
    def window_id(self):
        return self.native.window.id

    @lazy
    def window_id_i(self):
        return parse_window_id(self.window_id)

    def __repr__(self):
        return 'PA({})'.format(self.id, self.size)

    @lazy
    def running(self) -> Boolean:
        return self.command_pid.is_just

    @property
    def not_running(self) -> Boolean:
        return Boolean(not self.running)

    @property
    def _pipe_filter(self):
        return 'sed -u -e \'s/\r//g\' -e \'s/\x1b\[[0-9;?]*[mlK]//g\''

    def pipe(self, base):
        uid = os.getuid()
        tmpdir = Path(tempfile.gettempdir()) / 'myo-{}'.format(uid) / base
        tmpdir.mkdir(exist_ok=True, parents=True)
        (fh, fname) = tempfile.mkstemp(prefix='pane-', dir=str(tmpdir))
        self.native.cmd('pipe-pane', '{} > {}'.format(self._pipe_filter,
                                                      fname))
        return Just(Path(fname))

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
