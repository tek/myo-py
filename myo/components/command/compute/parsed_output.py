from typing import Generic, TypeVar

from amino import Dat, List

from myo.components.command.compute.parse_handlers import ParseHandlers
from myo.output.data.output import OutputEvent

A = TypeVar('A')
B = TypeVar('B')


class ParsedOutput(Generic[A, B], Dat['ParsedOutput[A, B]']):

    def __init__(
            self,
            handlers: ParseHandlers,
            original: List[OutputEvent[A, B]],
            filtered: List[OutputEvent[A, B]],
    ) -> None:
        self.handlers = handlers
        self.original = original
        self.filtered = filtered


__all__ = ('ParsedOutput',)
