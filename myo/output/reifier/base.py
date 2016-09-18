import abc

from amino import List

from myo.output.data import OutputLine, ParseResult
from myo.logging import Logging


class Reifier(Logging, metaclass=abc.ABCMeta):

    def __init__(self, vim) -> None:
        self.vim = vim

    @abc.abstractmethod
    def __call__(self, result: ParseResult) -> List[OutputLine]:
        ...


class LiteralReifier(Reifier):

    def __call__(self, result):
        return result.lines

__all__ = ('Reifier', 'LiteralReifier')
