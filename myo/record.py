from uuid import UUID

from ribosome.record import Record as RecordBase, uuid_field, field

from myo.ui.tmux.util import Ident


class Record(RecordBase):
    uuid = uuid_field()

    @property
    def ident(self):
        return self.uuid


class Named(Record):
    name = field(str)

    def has_ident(self, ident: Ident):
        attr = self.uuid if isinstance(ident, UUID) else self.name
        return attr == ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

    __str__ = __repr__

__all__ = ('Record',)
