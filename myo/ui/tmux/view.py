from numbers import Number

from trypnv.record import Record, maybe_field

from tryp import Just


class View(Record):
    min_size = maybe_field(Number)
    max_size = maybe_field(Number)
    fixed_size = maybe_field(Number)
    weight = maybe_field(Number)
    position = maybe_field(Number)

    @property
    def effective_weight(self):
        return Just(0) if self.fixed_size.is_just else self.weight

__all__ = ('View',)
