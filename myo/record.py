from trypnv.record import Record as RecordBase, uuid_field


class Record(RecordBase):
    uuid = uuid_field()

__all__ = ('Record',)
