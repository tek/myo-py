from numbers import Number

from ribosome.record import maybe_field, field

from amino import Just, L, List, _

from myo.record import Named


class View(Named):
    name = field(str)
    min_size = maybe_field(Number)
    max_size = maybe_field(Number)
    fixed_size = maybe_field(Number)
    weight = maybe_field(Number)
    position = maybe_field(Number)

    @property
    def effective_weight(self):
        return Just(0) if self.fixed_size.is_just else self.weight

    @property
    def size_desc(self):
        candidates = List(('min', self.min_size), ('max', self.max_size),
                          ('fix', self.fixed_size), ('weight', self.weight),
                          ('pos', self.position))
        def fmt(a, b):
            return b / L('| {} -> {}'.format)(a, _)
        return candidates.flat_map2(fmt).mk_string(' ')

__all__ = ('View',)
