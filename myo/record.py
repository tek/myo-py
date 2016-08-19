from uuid import UUID

from ribosome.record import Record as RecordBase, uuid_field, field

from myo.ui.tmux.util import Ident


class Record(RecordBase):
    uuid = uuid_field()

    def __str__(self):
        return super().__repr__()


class Named(Record):
    name = field(str)

    def has_ident(self, ident: Ident):
        attr = self.uuid if isinstance(ident, UUID) else self.name
        return attr == ident

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.name)

__all__ = ('Record',)
