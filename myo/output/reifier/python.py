from myo.output.reifier.base import Reifier as ReifierBase
from myo.output.data.output import OutputLineOld, EmptyLine
from myo.output.parser.python import FileEntry, ErrorEntry

from amino import List, Just, __


class Reifier(ReifierBase):

    def _format_file(self, entry: FileEntry):
        fun = entry.fun / ' {}'.format | ''
        return '{}  {}{}'.format(str(self._truncate(entry.path)), entry.line, fun)

    def _format_error(self, entry):
        return '{} {}'.format(entry.exc, entry.error)

    def _format_code(self, entry):
        return entry.code

    def _file(self, event, entry: FileEntry):
        code = entry.code / __.format_lines(Just(entry), self._format_code) | List() / __.set(indent=2)
        return entry.format_lines(Just(entry), self._format_file) + code

    def _error(self, event, entry: ErrorEntry):
        return (entry.format_lines(Just(event), self._format_error) +
                List(EmptyLine.create(event)))

    def _event(self, event):
        def dispatch(entry):
            return (
                self._file(event, entry)
                if isinstance(entry, FileEntry) else
                self._error(event, entry)
                if isinstance(entry, ErrorEntry) else
                List()
            )
        return event.lines // dispatch

    def __call__(self, result) -> List[OutputLineOld]:
        return result.events // self._event

__all__ = ('Reifier',)
