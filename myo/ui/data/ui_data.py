from amino import Dat, List, _, Nil

from myo.ui.data.space import Space


class UiData(Dat['UiData']):

    @staticmethod
    def cons(
        spaces: List[Space]=Nil,
    ) -> 'UiData':
        return UiData(
            spaces,
        )

    def __init__(self, spaces: List[Space]) -> None:
        self.spaces = spaces

    def replace_space(self, space: Space) -> 'UiData':
        return self.copy(spaces=self.spaces.replace_where(space, _.ident == space.ident))


__all__ = ('UiData',)
