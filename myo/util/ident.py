from uuid import UUID
from typing import Union

from amino import Maybe, List, L, _, Empty

from ribosome.record import field, Record, uuid_field


class Key(Record):
    uuid = uuid_field()
    name = field(str)

    @property
    def _str_extra(self):
        return super()._str_extra.cat(self.name)

Ident = Union[str, UUID, Key]


def contains_pane_ident(a: Maybe):
    tpes = List(UUID, str)
    bad = lambda a: not tpes.exists(L(isinstance)(a, _))
    err = 'must be Maybe[Ident]'
    return not a.exists(bad), err


def ident_field():
    return field(Maybe, initial=Empty(), invariant=contains_pane_ident)

__all__ = ('Ident', 'contains_pane_ident', 'ident_field', 'Key')
