import abc

from myo.logging import Logging


class VimCallback(Logging, metaclass=abc.ABCMeta):

    def __init__(self, target) -> None:
        self.target = target
        self.vim = self.target.root

    @abc.abstractmethod
    def __call__(self, data):
        ...

__all__ = ('VimCallback',)
