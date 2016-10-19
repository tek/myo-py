from uuid import UUID
from typing import Union

from amino import Maybe, List, L, _, Empty

from ribosome.record import field, Record, uuid_field

Ident = Union[str, UUID]


def contains_pane_ident(a: Maybe):
    tpes = List(UUID, str)
    bad = lambda a: not tpes.exists(L(isinstance)(a, _))
    err = 'must be Maybe[Ident]'
    return not a.exists(bad), err


def ident_field():
    return field(Maybe, initial=Empty(), invariant=contains_pane_ident)


class Key(Record):
    ident = uuid_field()
    name = field(str)

__all__ = ('Ident', 'contains_pane_ident', 'ident_field', 'Key')
