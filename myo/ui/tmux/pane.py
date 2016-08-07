from uuid import UUID

from tryp.task import task

from psutil import Process
from tryp import __, List, Boolean, Maybe, _
from tryp.lazy import lazy

from trypnv.record import maybe_field, field

from myo.ui.tmux.view import View
from myo.ui.tmux.adapter import Adapter
from myo.util import parse_int
from myo.ui.tmux.util import parse_window_id, parse_pane_id, PaneIdent


class Pane(View):
    id = maybe_field(int)
    shell_pid = maybe_field(int)
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

    def ident(self, ident: PaneIdent):
        attr = self.uuid if isinstance(ident, UUID) else self.name
        return attr == ident


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

    @lazy
    def running(self) -> Boolean:
        return self.command_pid.is_just

    @property
    def not_running(self) -> Boolean:
        return Boolean(not self.running)

__all__ = ('Pane', 'VimPane', 'PaneAdapter')
