import abc

from amino import List

from myo.output.data import OutputLine, ParseResult
from myo.util.callback import VimCallback


class Reifier(VimCallback):

    def __init__(self, vim) -> None:
        self.vim = vim

    @abc.abstractmethod
    def __call__(self, result: ParseResult) -> List[OutputLine]:
        ...


class LiteralReifier(Reifier):

    def __call__(self, result):
        return result.lines

__all__ = ('Reifier', 'LiteralReifier')
