import abc
from typing import Callable

from amino import List, Path, Either, __, L, _, Just
from amino.task import Task
from amino.lazy import lazy

from ribosome import NvimFacade
from ribosome.machine.state import RunScratchMachine
from ribosome.machine import Nop, Message

from myo.logging import Logging
from myo.output.data import ParseResult
from myo.output.machine import OutputMachine, OutputInit


class OutputHandler(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def parse(self, output: List[str], errfile: Path) -> Task[ParseResult]:
        ...

    @abc.abstractmethod
    def display(self, result: ParseResult) -> Task[Message]:
        ...


class CustomOutputHandler(OutputHandler):

    def __init__(self, vim: NvimFacade, handler: Callable[[str], ParseResult]
                 ) -> None:
        self.vim = vim
        self.handler = handler

    def parse(self, output: List[str], errfile: Path):
        return Task.call(self.handler, output)

    def display(self, result):
        ctor = L(OutputMachine)(self.vim, _, result, _)
        size = self.vim.pvar('scratch_size') | 10
        return (
            Task.now(RunScratchMachine(ctor, False, size=Just(size))) /
            (lambda a: Just(List(a.pub, OutputInit().pub)))
        )


class VimCompiler(OutputHandler):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    def parse(self, output: List[str], errfile: Path):
        r = ParseResult(head='errorformat')
        return (Task.call(self.vim.cmd_sync, 'cgetfile {}'.format(errfile))
                .replace(r))

    def display(self, result):
        copen = Task.call(self.vim.cmd_sync, 'copen')
        cfirst = Task.call(self.vim.cmd_sync, 'cfirst')
        return (copen + cfirst).replace(Just(Nop()))


class Parsing(CustomOutputHandler):

    def __init__(self, vim: NvimFacade, langs: List[str]) -> None:
        self.vim = vim
        self.langs = langs

    @lazy
    def parsers(self):
        mod = 'myo.output.parser'
        def create(lang):
            return Either.import_name('{}.{}'.format(mod, lang),
                                      'Parser').to_list
        return self.langs // create / (lambda a: a())

    def parse(self, output: List[str], errfile: Path):
        events = self.parsers // __.events(output)
        return Task.now(ParseResult(head='parsed', events=events))

__all__ = ('CustomOutputHandler', 'VimCompiler', 'Parsing')
