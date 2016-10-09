from amino import List, Just, __

from myo.output.parser.sbt import SbtOutputEvent, FileEntry
from myo.output.reifier.base import Reifier as ReifierBase
from myo.output.data import OutputLine, EmptyLine


class Reifier(ReifierBase):

    def _format_file(self, entry: FileEntry):
        return '{}  {}'.format(str(self._truncate(entry.path)), entry.line)

    def _format_error(self, entry):
        return entry.error

    def _format_code(self, entry):
        return entry.code

    def _sbt_event(self, event):
        return (
            event.file.format_lines(Just(event), self._format_file) +
            event.file.format_lines(Just(event), self._format_error,
                                    group=Just('Error')) +
            (event.code // __.format_lines(Just(event), self._format_code)) +
            List(EmptyLine.create(event))
        )

    def __call__(self, result) -> List[OutputLine]:
        return result.events.filter_type(SbtOutputEvent) // self._sbt_event

__all__ = ('Reifier',)
