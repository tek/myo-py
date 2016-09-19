from myo.output.parser.sbt import SbtOutputEvent
from myo.output.reifier.base import Reifier as ReifierBase
from myo.output.data import OutputLine
from myo.util import parse_callback_spec

from amino import List, L, _, Just


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

    def _sbt_event(self, event, error, col):
        return (
            event.file.format_output_lines(Just(event),
                                           L(self._format_file)(_, col)) +
            error.format_output_lines(Just(event), self._format_error)
        )

    def _event(self, event):
        if isinstance(event, SbtOutputEvent):
            return (
                (event.error & event.col)
                .map2(L(self._sbt_event)(event, _, _)) | List()
            )
        else:
            return List()

    def __call__(self, result) -> List[OutputLine]:
        return result.events // self._event

__all__ = ('Reifier',)
