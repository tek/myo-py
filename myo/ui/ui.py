from amino import Dat, Maybe, Boolean
from amino.boolean import false

from chiasma.util.id import Ident

from ribosome.trans.handler import Trans
from ribosome.trans.api import trans


@trans.free.result()
def owns_no_pane(ident: Ident) -> Boolean:
    return false


class Ui(Dat['Ui']):

    @staticmethod
    def cons(
            owns_pane: Trans=owns_no_pane,
            render: Trans=None,
            open_pane: Trans=None,
            open_window: Trans=None,
            open_space: Trans=None,
    ) -> 'Ui':
        return Ui(
            owns_pane,
            Maybe.optional(render),
            Maybe.optional(open_pane),
            Maybe.optional(open_window),
            Maybe.optional(open_space),
        )

    def __init__(
            self,
            owns_pane: Trans,
            render: Maybe[Trans],
            open_pane: Maybe[Trans],
            open_window: Maybe[Trans],
            open_space: Maybe[Trans],
    ) -> None:
        self.owns_pane = owns_pane
        self.render = render
        self.open_pane = open_pane
        self.open_window = open_window
        self.open_space = open_space


__all__ = ('Ui',)
