import os

import libtmux
from libtmux import formats, exc

from amino import List, Map, Either, Try, Lists, _

from myo.tmux.native.pane import NativePane


class NativeWindow(libtmux.Window):

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
        return Lists.wrap(NativePane(window=self, **pane) for pane in self._panes)

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

    def create_pane(self) -> Either[str, NativePane]:
        return Try(self.split_window)

    def pane(self, id: str) -> Either[str, NativePane]:
        return self.panes.find(_.id == id).to_either(lambda: f'no pane `{id}` in {self}')


__all__ = ('NativeWindow',)
