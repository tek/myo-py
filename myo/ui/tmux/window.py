import os
from typing import Callable

from lenses import lens

from libtmux import formats, exc
from libtmux.window import Window as LTWindow

from amino import List, __, _, Maybe, Map
from amino.lazy import lazy

from ribosome.record import field, maybe_field

from myo.ui.tmux.adapter import Adapter
from myo.ui.tmux.pane import PaneAdapter, Pane, NativePane
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.util import parse_window_id
from myo.record import Named, Record
from myo.logging import Logging


class Size(Record):
    width = field(int)
    height = field(int)

    @staticmethod
    def create(width, height):
        return Size(width=width, height=height)

    @property
    def _str_extra(self):
        return List(self.width, self.height)

    @property
    def tuple(self):
        return self.width, self.height


class Window(Named):
    id = maybe_field(int)
    root = field(Layout)
    size = maybe_field(Size)

    @property
    def desc(self):
        id = self.id / ' @{}'.format | ''
        return 'W{}'.format(id)

    def pane_lens(self, f: Callable[[Pane], Maybe]):
        return self.root.pane_lens(f) / lens().root.add_lens

    @property
    def _str_extra(self):
        return super()._str_extra.cat(self.root)


class VimWindow(Window):
    window_name = '<vim>'

    def __new__(cls, *a, name=None, **kw):
        n = Maybe(name) | VimWindow.window_name
        return super().__new__(cls, *a, name=n, **kw)

    @property
    def desc(self):
        return 'V{}'.format(super().desc)


class NativeWindow(LTWindow, Logging):

    def __init__(self, session=None, **kwargs):
        if not session:
            raise ValueError('Window requires a Session, session=Session')
        self.session = session
        self.server = self.session.server
        if 'window_id' not in kwargs:
            raise ValueError('Window requires a `window_id`')
        self._window_id = kwargs['window_id']
        self._data = Map(kwargs) + ('id', self._window_id)

    @property
    def _info(self):
        return self._data

    def _list_panes(self):
        pformats = [
            'session_name', 'session_id',
            'window_index', 'window_id',
            'window_name'
        ] + formats.PANE_FORMATS
        tmux_formats = ['#{%s}\t' % f for f in pformats]
        proc = self.cmd('list-panes', '-F%s' % ''.join(tmux_formats))
        panes = proc.stdout
        pformats = [
            'session_name', 'session_id',
            'window_index', 'window_id', 'window_name'
        ] + formats.PANE_FORMATS
        panes = [dict(zip(
            pformats, window.split('\t'))) for window in panes]
        panes = [
            dict(
                (k, v) for k, v in window.items()
                if v or
                k == 'pane_current_path'
            )   # preserve pane_current_path, in case it entered a new process
                # where we may not get a cwd from.
            for window in panes
        ]
        return panes

    def list_panes(self):
        return [NativePane(window=self, **pane) for pane in self._panes]

    @property
    def attached_pane(self):
        return (List.wrap(self.panes)
                .find(lambda a: a._info.get('pane_active') == '1'))

    def split_window(
            self,
            target=None,
            start_directory=None,
            attach=True,
            vertical=True
    ):
        pformats = ['session_name', 'session_id',
                    'window_index', 'window_id'] + formats.PANE_FORMATS
        tmux_formats = ['#{%s}\t' % f for f in pformats]
        tmux_args = tuple()
        if target:
            tmux_args += ('-t%s' % target,)
        else:
            tmux_args += ('-t%s' % self.panes[0].get('pane_id'),)
        if vertical:
            tmux_args += ('-v',)
        else:
            tmux_args += ('-h',)
        tmux_args += (
            '-P', '-F%s' % ''.join(tmux_formats)
        )
        if start_directory:
            start_directory = os.path.expanduser(start_directory)
            tmux_args += ('-c%s' % start_directory,)
        if not attach:
            tmux_args += ('-d',)
        pane = self.cmd(
            'split-window',
            *tmux_args
        )
        if pane.stderr:
            raise exc.LibTmuxException(pane.stderr)
            if 'pane too small' in pane.stderr:
                pass
            raise exc.LibTmuxException(pane.stderr, self._info, self.panes)
        else:
            pane = pane.stdout[0]
            pane = dict(zip(pformats, pane.split('\t')))
            pane = dict((k, v) for k, v in pane.items() if v)
        return NativePane(window=self, **pane)


class WindowAdapter(Adapter):

    @lazy
    def panes(self):
        return List.wrap(self.native.panes) / PaneAdapter

    def pane_by_id(self, id: int):
        return self.panes.find(__.id_i.contains(id))

    @lazy
    def id(self):
        return self.native._window_id

    @lazy
    def id_i(self):
        return parse_window_id(self.id)

    @lazy
    def size(self):
        return int(self.native.width), int(self.native.height)

    @property
    def active_pane(self):
        return self.panes.find(_.active)

    def kill(self):
        self.native.kill_window()

    @property
    def name(self):
        return self.native.name

__all__ = ('WindowAdapter', 'Window')
