from amino import Dat, Maybe, Boolean
from amino.boolean import false

from chiasma.util.id import Ident

from ribosome.compute.prog import Program
from ribosome.compute.api import prog


@prog.strict
def owns_no_pane(ident: Ident) -> Boolean:
    return false


class Ui(Dat['Ui']):

    @staticmethod
    def cons(
            owns_pane: Program=owns_no_pane,
            render: Program=None,
            open_pane: Program=None,
            open_window: Program=None,
            open_space: Program=None,
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
            owns_pane: Program,
            render: Maybe[Program],
            open_pane: Maybe[Program],
            open_window: Maybe[Program],
            open_space: Maybe[Program],
    ) -> None:
        self.owns_pane = owns_pane
        self.render = render
        self.open_pane = open_pane
        self.open_window = open_window
        self.open_space = open_space


__all__ = ('Ui',)
