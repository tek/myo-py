from amino import List, Just, __

from myo.output.parser.scala import ScalaOutputEvent, FileEntry
from myo.output.reifier.base import Reifier as ReifierBase
from myo.output.data.output import OutputLineOld, EmptyLine


class Reifier(ReifierBase):

    def _format_file(self, entry: FileEntry):
        return '{}  {}'.format(str(self._truncate(entry.path)), entry.line)

    def _format_error(self, entry):
        return entry.error

    def _format_code(self, entry):
        return entry.code

    def _scala_event(self, event):
        return (
            event.file.format_lines(Just(event), self._format_file) +
            event.file.format_lines(Just(event), self._format_error,
                                    group=Just('Error')) +
            (event.code // __.format_lines(Just(event), self._format_code)) +
            List(EmptyLine.create(event))
        )

    def __call__(self, result) -> List[OutputLineOld]:
        return result.events.filter_type(ScalaOutputEvent) // self._scala_event

__all__ = ('Reifier',)
