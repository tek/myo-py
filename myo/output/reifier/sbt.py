from myo.output.parser.sbt import SbtOutputEvent
from myo.output.reifier.base import Reifier as ReifierBase
from myo.output.data import OutputLine
from myo.util import parse_callback_spec

from amino import List, L, _, Just, __


class Reifier(ReifierBase):

    def _truncate(self, path):
        return (
            self.vim.vars.p('path_truncator') /
            parse_callback_spec //
            _.join /
            (lambda a: a(path)) |
            path
        )

    def _format_file(self, entry, col):
        return '{}  {}'.format(str(self._truncate(entry.path)), col.col)

    def _format_error(self, entry):
        return entry.error

    def _format_code(self, entry):
        return entry.code

    def _sbt_event(self, event, code, col):
        code_line = (code.format_output_lines(Just(event), self._format_code) /
                     __.set(indent=4))
        return (
            event.file.format_output_lines(Just(event),
                                           L(self._format_file)(_, col)) +
            event.file.format_output_lines(Just(event),
                                           L(self._format_error)(_),
                                           group=Just('Error')) +
            code_line
        )

    def _event(self, event):
        return (
            (event.code & event.col)
            .map2(L(self._sbt_event)(event, _, _)) | List()
        )

    def __call__(self, result) -> List[OutputLine]:
        return result.events.filter_type(SbtOutputEvent) // self._event

__all__ = ('Reifier',)
