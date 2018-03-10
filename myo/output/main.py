import abc
from typing import Callable

from amino import List, Path, Either, __, L, _, Just, Maybe, Map, Empty, Nil
from amino.io import IO
from amino.lazy import lazy

from ribosome import NvimFacade
from ribosome.util.callback import VimCallback

from myo.logging import Logging
from myo.output.data import ParseResult


class OutputHandler(Logging, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def parse(self, output: List[str], errfile: Path) -> IO[ParseResult]:
        ...

    # @abc.abstractmethod
    # def display(self, result: ParseResult, jump: Maybe[Callable]
    #             ) -> IO[List[Message]]:
    #     ...


# `IfUnhandled` part to the core machine, using transition priorities
class CustomOutputHandler(OutputHandler):

    def __init__(self, vim: NvimFacade, handler: Callable[[str], ParseResult]
                 ) -> None:
        self.vim = vim
        self.handler = handler

    def parse(self, output: List[str], errfile: Path):
        return IO.call(self.handler, output)

#     def display(self, result: ParseResult, options: Map[str, str]):
#         ctor = L(OutputMachine)(self.vim, _, result, _, options)
#         size = self.vim.vars.p('scratch_size') | 10
#         msg = SetResult(result, options)
#         opt = Map(use_tab=False, size=Just(size), wrap=True, init=msg)
#         run = RunScratchMachine(ctor, options=opt)
#         return IO.just(IfUnhandled(msg, run).pub)


class VimCompiler(OutputHandler, VimCallback):

    def __call__(self, data):
        return Empty()

    def parse(self, output: List[str], errfile: Path):
        r = ParseResult(head=List('errorformat'))
        return IO.call(self.vim.cmd_sync, 'cgetfile {}'.format(errfile)).replace(r)

    def display(self, result, jump):
        copen = IO.call(self.vim.cmd_sync, 'copen')
        cfirst = IO.call(self.vim.cmd_sync, 'cfirst')
        return (copen + cfirst).replace(Just(Nop()))


class Parsing(CustomOutputHandler):

    def __init__(self, vim: NvimFacade, langs: List[str]) -> None:
        self.vim = vim
        self.langs = langs

    @lazy
    def parsers(self):
        mod = 'myo.output.parser'
        def create(lang):
            return Either.import_name('{}.{}'.format(mod, lang), 'Parser').to_list
        return self.langs // create / (lambda a: a())

    def parse(self, output: List[str], errfile: Path):
        events = self.parsers // __.events(output)
        return IO.now(ParseResult(Nil, events, self.langs))

__all__ = ('CustomOutputHandler', 'VimCompiler', 'Parsing')
