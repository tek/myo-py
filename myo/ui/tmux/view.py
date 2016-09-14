from numbers import Number

from ribosome.record import maybe_field, field, bool_field

from amino import Just, L, List, _

from myo.record import Named


class View(Named):
    name = field(str)
    min_size = maybe_field(Number)
    max_size = maybe_field(Number)
    fixed_size = maybe_field(Number)
    minimized = bool_field()
    minimized_size = maybe_field(Number)
    weight = maybe_field(Number)
    position = maybe_field(Number)

    @property
    def _minimized_size(self):
        return self.minimized_size | 2

    @property
    def effective_weight(self):
        return (Just(0) if self.fixed_size.is_just or self.minimized else
                self.weight)

    @property
    def effective_fixed_size(self):
        return self.minimized.cata(Just(self._minimized_size), self.fixed_size)

    @property
    def size_desc(self):
        candidates = List(
            ('min', self.min_size), ('max', self.max_size),
            ('fix', self.fixed_size), ('weight', self.weight),
            ('pos', self.position), ('mini', self.minimized_size)
        )
        def fmt(a, b):
            return b / L('| {} -> {}'.format)(a, _)
        return candidates.flat_map2(fmt).mk_string(' ')

__all__ = ('View',)
