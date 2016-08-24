import abc

from myo.logging import Logging
from myo.output.data import OutputEvent

from amino import List

from ribosome import NvimFacade


class ParserBase(Logging):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    @abc.abstractmethod
    def events(self, output: List[str]) -> List[OutputEvent]:
        ...

__all__ = ('ParserBase',)
