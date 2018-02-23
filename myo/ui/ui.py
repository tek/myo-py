from amino import Dat, Maybe, Boolean
from amino.boolean import false

from chiasma.util.id import Ident

from ribosome.trans.handler import TransHandler
from ribosome.trans.api import trans


@trans.free.result()
def owns_no_pane(ident: Ident) -> Boolean:
    return false


class Ui(Dat['Ui']):

    @staticmethod
    def cons(
            owns_pane: TransHandler=owns_no_pane,
            render: TransHandler=None,
            open_pane: TransHandler=None,
            open_window: TransHandler=None,
            open_space: TransHandler=None,
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
            owns_pane: TransHandler,
            render: Maybe[TransHandler],
            open_pane: Maybe[TransHandler],
            open_window: Maybe[TransHandler],
            open_space: Maybe[TransHandler],
    ) -> None:
        self.owns_pane = owns_pane
        self.render = render
        self.open_pane = open_pane
        self.open_window = open_window
        self.open_space = open_space


__all__ = ('Ui',)
