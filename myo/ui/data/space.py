from uuid import uuid4

from amino import Dat, List, Nil, _

from myo.ui.data.window import Window
from myo.util import Ident


class Space(Dat['Space']):

    @staticmethod
    def cons(
            ident: Ident=None,
            windows: List[Window]=Nil,
    ) -> 'Space':
        return Space(
            ident or uuid4(),
            windows,
        )

    def __init__(self, ident: Ident, windows: List[Window]) -> None:
        self.ident = ident
        self.windows = windows

    def replace_window(self, window: Window) -> 'Space':
        return self.copy(windows=self.windows.replace_where(window, _.ident == window.ident))

__all__ = ('Space',)
