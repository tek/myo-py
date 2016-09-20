import abc

from myo.logging import Logging


class VimCallback(Logging, metaclass=abc.ABCMeta):

    def __init__(self, vim) -> None:
        self.vim = vim

    @abc.abstractmethod
    def __call__(self, data):
        ...

__all__ = ('VimCallback',)
