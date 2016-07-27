from numbers import Number

from trypnv.record import Record, maybe_field


class View(Record):
    min_size = maybe_field(Number)
    max_size = maybe_field(Number)
    weight = maybe_field(Number)

__all__ = ('View',)
