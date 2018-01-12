import libtmux

from amino import Dat, Maybe

from myo.util import Ident


class Session(Dat['Session']):

    @staticmethod
    def cons(
            space: Ident,
            id: str=None,
    ) -> None:
        return Session(
            space,
            Maybe.check(id),
        )

    @staticmethod
    def from_native(space: Ident, session: libtmux.Session) -> 'Session':
        return Session.cons(space, session.id)

    def __init__(self, space: Ident, id: Maybe[str]) -> None:
        self.space = space
        self.id = id


__all__ = ('Session',)
