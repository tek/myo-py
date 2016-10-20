from uuid import UUID

from ribosome.record import Record as RecordBase, uuid_field, field

from amino import List

from myo.util import Ident
from myo.util.ident import Key


class Record(RecordBase):
    uuid = uuid_field()

    @property
    def ident(self) -> Ident:
        return self.uuid


class Named(Record):
    name = field(str)

    def has_uuid(self, uuid: UUID):
        return self.uuid == uuid

    def has_name(self, name: str):
        return self.name == name

    def has_key(self, key: Key):
        return self.has_uuid(key.uuid) or self.has_name(key.name)

    def has_ident(self, ident: Ident):
        matcher = (
            self.has_uuid
            if isinstance(ident, UUID) else
            self.has_key
            if isinstance(ident, Key) else
            self.has_name
        )
        return matcher(ident)

    @property
    def _str_extra(self):
        return List(self.name)

__all__ = ('Record',)
