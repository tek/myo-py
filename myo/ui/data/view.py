from uuid import uuid4

from amino import Boolean, ADT

from myo.util import Ident


class View(ADT['View']):
    pass


class Layout(View):

    @staticmethod
    def cons(
            ident: Ident=None,
            vertical: Boolean=True,
    ) -> 'Layout':
        return Layout(
            ident or uuid4(),
            vertical,
        )

    def __init__(self, ident: Ident, vertical: Boolean) -> None:
        self.ident = ident
        self.vertical = vertical


class Pane(View):

    @staticmethod
    def cons(
            ident: Ident=None,
            open: bool=False,
    ) -> 'Pane':
        return Pane(
            ident or uuid4(),
            Boolean(open),
        )

    def __init__(self, ident: Ident, open: Boolean) -> None:
        self.ident = ident
        self.open = open


__all__ = ('View', 'Layout', 'Pane')
