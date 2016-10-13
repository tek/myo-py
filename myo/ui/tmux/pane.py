import abc
from pathlib import Path
import tempfile
import os

from psutil import Process

from libtmux.pane import Pane as LTPane

from amino.task import task

from amino import __, List, Boolean, Maybe, _, Map, Just, Try, L
from amino.lazy import lazy

from ribosome.record import maybe_field, either_field, bool_field

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
    pin = bool_field()
    focus = bool_field()
    kill = bool_field()

    @property
    def id_s(self):
        return self.id / '%{}'.format

    @property
    def desc(self):
        id = self.id / ' %{}'.format | ''
        pid = self.pid / ' | pid -> {}'.format | ''
        pin = ' !' if self.pin else ''
        return 'P{} \'{}\'{}{} {}'.format(id, self.name, pin, pid,
                                          self.size_desc)

    def open(self, pa: 'PaneAdapter'):
        return self.set(id=pa.id_i.to_maybe, shell_pid=pa.pid.to_maybe,
                        session_id=pa.session_id_i, window_id=pa.window_id_i)

    @property
    def _str_extra(self):
        return self.id.to_list + super()._str_extra


class VimPane(Pane):
    pane_name = '<vim>'

    def __new__(cls, *a, name=None, **kw):
        n = Maybe(name) | VimPane.pane_name
        return super().__new__(cls, *a, name=n, **kw)

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

    @property
    def command_pid(self) -> Maybe[int]:
        return (
            self.pid //
            L(Try)(Process, _) /
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


class NativePane(LTPane):

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


class PaneAdapter(Adapter, PaneI):

    @lazy
    def id(self):
        return self.native._pane_id

    @lazy
    def id_i(self):
        return parse_pane_id(self.id)

    @property
    def _raw_pid(self):
        return Try(lambda: self.native.pid)

    @task
    def resize(self, size, horizontal):
        f = __.set_width if horizontal else __.set_height
        return f(size)(self.native)

    @property  # type: ignore
    @task
    def kill(self):
        return self.cmd('kill-pane')

    def split(self, horizontal):
        return self.native.split_window(vertical=not horizontal)

    @lazy
    def width(self):
        return int(self.native.width)

    @lazy
    def height(self):
        return int(self.native.height)

    @lazy
    def size(self):
        return self.width, self.height

    @lazy
    def left(self):
        return int(self.native.left)

    @lazy
    def top(self):
        return int(self.native.top)

    @lazy
    def position(self):
        return self.left, self.top

    def send_keys(self, cmd, enter=True, suppress_history=True):
        return self.native.send_keys(cmd, enter=enter,
                                     suppress_history=suppress_history)

    @property
    def capture(self):
        return List.wrap(self.cmd('capture-pane', '-p'))

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
        return 'PA({}, {}, {})'.format(self.id, self.size, self.position)

    @property
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
        self.cmd('pipe-pane', '{} > {}'.format(self._pipe_filter, fname))
        return Just(Path(fname))

    def move_above(self, other: 'PaneAdapter'):
        self.cmd('move-pane', '-b', '-s', other.id)

    def move_below(self, other: 'PaneAdapter'):
        self.cmd('move-pane', '-s', other.id)

    def swap(self, other: 'PaneAdapter'):
        self.cmd('swap-pane', '-d', '-s', other.id)

    def __eq__(self, other):
        return isinstance(other, PaneAdapter) and self.id == other.id

    @property
    def active(self):
        return self.native.active == '1'

    def focus(self):
        self.native.select_pane()

    def run_command(self, line):
        self.quit_copy_mode()
        self.send_keys(line, suppress_history=False)

    @property
    def in_copy_mode(self):
        return self.native.in_mode == '1'

    def quit_copy_mode(self):
        if self.in_copy_mode:
            self.send_keys('C-c')

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
