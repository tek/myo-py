from typing import Callable

from amino import List, __, _

from lenses import lens

from ribosome.record import field, list_field

from myo.record import Record
from myo.ui.tmux.session import Session, VimSession
from myo.ui.tmux.window import VimWindow, Window
from myo.ui.tmux.layout import VimLayout, Layout
from myo.ui.tmux.pane import VimPane
from myo.ui.tmux.util import Ident

_is_vim_session = lambda a: isinstance(a, VimSession)
_is_vim_window = lambda a: isinstance(a, VimWindow)
_is_vim_layout = lambda a: isinstance(a, VimLayout)
_is_vim_pane = lambda a: isinstance(a, VimPane)


class TmuxState(Record):
    sessions = list_field()
    instance_id = field(str, initial='',
                        factory=lambda a: a if a else List.random_string(5))

    @property
    def _str_extra(self):
        return self.sessions

    def session_lens(self, pred: Callable[[Session], bool]):
        return self.attr_lens_pred(_.sessions, pred) / __.bind(self)

    @property
    def vim_session(self):
        return self.sessions.find(_is_vim_session)

    @property
    def vim_session_lens(self):
        return (self.sessions.find_lens_pred(_is_vim_session) /
                lens(self).sessions.add_lens)

    def window_lens(self, pred: Callable[[Window], bool]):
        sub = __.attr_lens_pred(_.windows, pred)
        return self.attr_lens(_.sessions, sub) / __.bind(self)

    def window_lens_ident(self, ident: Ident):
        return self.window_lens(__.has_ident(ident))

    @property
    def vim_window(self):
        return self.vim_session // __.windows.find(_is_vim_window)

    @property
    def vim_window_lens(self):
        return self.window_lens(_is_vim_window)

    def layout_lens(self, pred: Callable[[Layout], bool]):
        lay_sub = __.root.layout_lens(pred).map(lens().root.add_lens)
        win_sub = __.attr_lens(_.windows, lay_sub)
        return self.attr_lens(_.sessions, win_sub) / __.bind(self)

    def layout_lens_ident(self, ident: Ident):
        return self.layout_lens(__.has_ident(ident))

    @property
    def vim_layout(self):
        return self.vim_window // __.root.layouts.find(_is_vim_layout)

    @property
    def vim_layout_lens(self):
        return self.layout_lens(_is_vim_layout)

    def pane_lens(self, pred: Callable[[Layout], bool]):
        lay_sub = __.root.pane_lens(pred).map(lens().root.add_lens)
        win_sub = __.attr_lens(_.windows, lay_sub)
        return self.attr_lens(_.sessions, win_sub) / __.bind(self)

    def pane_lens_ident(self, ident: Ident):
        return self.pane_lens(__.has_ident(ident))

    @property
    def vim_pane(self):
        return self.vim_layout / _.panes / _.head

    @property
    def all_windows(self):
        return self.sessions // _.windows

    def window(self, ident: Ident):
        return self.all_windows.find(__.has_ident(ident))

    @property
    def all_panes(self):
        return self.all_windows // _.root.all_panes

    def pane(self, ident):
        return self.all_panes.find(__.has_ident(ident))

    @property
    def possibly_open_panes(self):
        return (
            self.all_panes
            .filter(_.id.is_just)
            .filter(lambda a: not _is_vim_pane(a))
        )

__all__ = ('TmuxState',)
