from amino import Dat, Maybe

from chiasma.util.id import Ident
from chiasma.data.tmux import Views


class TmuxData(Dat['TmuxData']):

    @staticmethod
    def cons(views: Views=None, vim_pane: Ident=None) -> 'TmuxData':
        return TmuxData(
            views or Views.cons(),
            Maybe.optional(vim_pane)
        )

    def __init__(self, views: Views, vim_pane: Maybe[Ident]) -> None:
        self.views = views
        self.vim_pane = vim_pane


__all__ = ('TmuxData',)
