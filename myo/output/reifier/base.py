import abc

from amino import List, __
from amino.lazy import lazy

from ribosome.machine.helpers import TransitionHelpers
from ribosome.util.callback import VimCallback

from myo.output.data import OutputLine, ParseResult


class Reifier(VimCallback, TransitionHelpers):

    @abc.abstractmethod
    def __call__(self, result: ParseResult) -> List[OutputLine]:
        ...

    @lazy
    def _truncator(self):
        return self._callback('path_truncator')

    def _truncate(self, path):
        return self._truncator / __(path) | path


class LiteralReifier(Reifier):

    def __call__(self, result):
        return result.lines

__all__ = ('Reifier', 'LiteralReifier')
