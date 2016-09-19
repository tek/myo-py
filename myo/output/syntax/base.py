import abc

from myo.logging import Logging


class OutputSyntax(Logging, metaclass=abc.ABCMeta):

    def __init__(self, vim) -> None:
        self.vim = vim

    @abc.abstractmethod
    def __call__(self, lines):
        pass

__all__ = ('OutputSyntax',)
