from uuid import uuid4
from numbers import Number

from amino import Boolean, ADT, Maybe, Dat, Just

from myo.util import Ident


class ViewGeometry(Dat['ViewGeometry']):

    @staticmethod
    def cons(
            min_size: Number=None,
            max_size: Number=None,
            fixed_size: Number=None,
            minimized_size: Number=None,
            weight: Number=None,
            position: Number=None,
    ) -> 'ViewGeometry':
        return ViewGeometry(
            Maybe.check(min_size),
            Maybe.check(max_size),
            Maybe.check(fixed_size),
            Maybe.check(minimized_size),
            Maybe.check(weight),
            Maybe.check(position),
        )

    def __init__(
            self,
            min_size: Maybe[Number],
            max_size: Maybe[Number],
            fixed_size: Maybe[Number],
            minimized_size: Maybe[Number],
            weight: Maybe[Number],
            position: Maybe[Number],
    ) -> None:
        self.min_size = min_size
        self.max_size = max_size
        self.fixed_size = fixed_size
        self.minimized_size = minimized_size
        self.weight = weight
        self.position = position


class View(ADT['View']):

    def __init__(self, ident: Ident, geometry: ViewGeometry, minimized: Boolean) -> None:
        self.ident = ident
        self.geometry = geometry
        self.minimized = minimized

    @property
    def _minimized_size(self) -> int:
        return self.geometry.minimized_size | 2

    @property
    def effective_weight(self) -> Maybe[int]:
        return Just(0) if self.geometry.fixed_size.present or self.minimized else self.geometry.weight

    @property
    def effective_fixed_size(self) -> Maybe[int]:
        return self.minimized.cata(Just(self._minimized_size), self.geometry.fixed_size)


class Layout(View):

    @staticmethod
    def cons(
            ident: Ident=None,
            geometry: ViewGeometry=None,
            minimized: bool=False,
            vertical: bool=True,
    ) -> 'Layout':
        return Layout(
            ident or uuid4(),
            geometry or ViewGeometry.cons(),
            Boolean(minimized),
            Boolean(vertical),
        )

    def __init__(self, ident: Ident, geometry: ViewGeometry, minimized: Boolean, vertical: Boolean) -> None:
        super().__init__(ident, geometry, minimized)
        self.vertical = vertical


class Pane(View):

    @staticmethod
    def cons(
            ident: Ident=None,
            geometry: ViewGeometry=None,
            minimized: bool=False,
            open: bool=False,
    ) -> 'Pane':
        return Pane(
            ident or uuid4(),
            geometry or ViewGeometry.cons(),
            Boolean(minimized),
            Boolean(open),
        )

    def __init__(self, ident: Ident, geometry: ViewGeometry, minimized: Boolean, open: Boolean) -> None:
        super().__init__(ident, geometry, minimized)
        self.open = open


__all__ = ('View', 'Layout', 'Pane')
