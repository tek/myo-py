import abc
from typing import Callable

from amino import List, Path, Either, __, L, _, Just, Maybe, Map
from amino.task import Task
from amino.lazy import lazy

from ribosome import NvimFacade
from ribosome.machine.state import RunScratchMachine, IfUnhandled
from ribosome.machine import Nop, Message

from myo.logging import Logging
from myo.output.data import ParseResult
from myo.output.machine import OutputMachine, SetResult


class OutputHandler(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def parse(self, output: List[str], errfile: Path) -> Task[ParseResult]:
        ...

    @abc.abstractmethod
    def display(self, result: ParseResult, jump: Maybe[Callable]
                ) -> Task[List[Message]]:
        ...


class CustomOutputHandler(OutputHandler):

    def __init__(self, vim: NvimFacade, handler: Callable[[str], ParseResult]
                 ) -> None:
        self.vim = vim
        self.handler = handler

    def parse(self, output: List[str], errfile: Path):
        return Task.call(self.handler, output)

    def display(self, result: ParseResult, options: Map[str, str]):
        ctor = L(OutputMachine)(self.vim, _, result, _, options)
        size = self.vim.vars.p('scratch_size') | 10
        msg = SetResult(result, options)
        opt = Map(use_tab=False, size=Just(size), wrap=True, init=msg)
        run = RunScratchMachine(ctor, options=opt)
        return Task.just(IfUnhandled(msg, run).pub)


class VimCompiler(OutputHandler):

    def __init__(self, vim: NvimFacade) -> None:
        self.vim = vim

    def parse(self, output: List[str], errfile: Path):
        r = ParseResult(head=List('errorformat'))
        return (Task.call(self.vim.cmd_sync, 'cgetfile {}'.format(errfile))
                .replace(r))

    def display(self, result, jump):
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
        return Task.now(ParseResult(head=List('parsed'), events=events,
                                    langs=self.langs))

__all__ = ('CustomOutputHandler', 'VimCompiler', 'Parsing')
