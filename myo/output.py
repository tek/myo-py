import abc
from typing import Callable

from amino import List, _, Path
from amino.task import Task

from ribosome.record import list_field, field
from ribosome import NvimFacade

from myo.record import Record
from myo.logging import Logging


class OutputEntry(Record):
    text = field(str)

    @property
    def formatted(self):
        return self.text


class OutputEvent(Record):
    head = field(str)
    entries = list_field(OutputEntry)

    @property
    def display_lines(self):
        return (self.entries / _.formatted).cons(self.head)


class ParseResult(Record):
    head = field(str)
    events = list_field(OutputEvent)

    @property
    def display_lines(self):
        return (self.events // _.display_lines).cons(self.head)


class OutputHandler(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def parse(self, output: List[str], errfile: Path) -> Task[ParseResult]:
        ...

    @abc.abstractmethod
    def display(self, result: ParseResult) -> Task:
        ...


class CustomOutputHandler(OutputHandler):

    def __init__(self, vim: NvimFacade, handler: Callable[[str], ParseResult]
                 ) -> None:
        self.vim = vim
        self.handler = handler

    def parse(self, output: List[str], errfile: Path):
        return Task.call(self.handler, output)

    def display(self, result):
        open_tab = Task(self.vim.tabnew)
        set_buffer = Task(
            lambda: self.vim.tab.buffer.set_content(result.display_lines))
        return open_tab + set_buffer


class VimCompiler(OutputHandler):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    def parse(self, output: List[str], errfile: Path):
        r = ParseResult(head='errorformat')
        return (Task.call(self.vim.cmd_sync, 'cgetfile {}'.format(errfile))
                .replace(r))

    def display(self, result):
        return Task.call(self.vim.cmd_sync, 'cfirst')

__all__ = ('CustomOutputHandler', 'VimCompiler')
