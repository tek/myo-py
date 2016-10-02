from uuid import UUID

from ribosome.record import Record as RecordBase, uuid_field, field

from amino import List

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

    @property
    def _str_extra(self):
        return List(self.name)

__all__ = ('Record',)
