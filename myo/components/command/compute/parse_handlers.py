from typing import Callable, TypeVar, Generic

from amino import Dat, List, Maybe, Either, Path, Nothing, Nil, do, Do

from ribosome.nvim.io.state import NS
from ribosome.nvim.syntax.syntax import Syntax

from myo.components.command.compute.tpe import CommandRibosome
from myo.output.data.output import OutputEvent
from myo.output.config import ParseConfig
from myo.output.data.report import DisplayLine, PlainDisplayLine

A = TypeVar('A')
B = TypeVar('B')
OutputFilter = Callable[[List[OutputEvent[A, B]]], List[OutputEvent[A, B]]]
FirstError = Callable[[OutputEvent[A, B]], NS[CommandRibosome, int]]
PathFormatter = Callable[[Path], NS[CommandRibosome, str]]
Reporter = Callable[[PathFormatter, OutputEvent[A, B]], NS[CommandRibosome, List[List[DisplayLine]]]]
SyntaxCons = Callable[[], NS[CommandRibosome, Syntax]]


def default_first_error(output: List[OutputEvent[A, B]]) -> NS[CommandRibosome, int]:
    return NS.pure(0)


def default_path_formatter(path: Path) -> NS[CommandRibosome, str]:
    return NS.pure(str(path))


def verbatim_report(formatter: PathFormatter, event: OutputEvent[A, B]) -> NS[CommandRibosome, List[str]]:
    return NS.pure(event.lines.map(lambda a: PlainDisplayLine(a.text)))


def no_syntax() -> NS[CommandRibosome, Syntax]:
    return NS.pure(Syntax.cons())


class ParseHandlers(Generic[A, B], Dat['ParseHandlers[A, B]']):

    @staticmethod
    def from_config(config: ParseConfig) -> Either[str, 'ParseHandlers']:
        return ParseHandlers.resolve(
            config.filter,
            config.first_error,
            config.path_formatter,
            config.reporter,
            config.syntax,
        )

    @staticmethod
    @do(Either[str, 'ParseHandlers'])
    def resolve(
            filter: List[str],
            first_error: Maybe[str],
            path_formatter: Maybe[str],
            reporter: Maybe[str],
            syntax: Maybe[str],
    ) -> Do:
        filter_handlers = yield filter.traverse(Either.import_path, Either)
        first_error_handler = yield first_error.traverse(Either.import_path, Either)
        path_formatter_handler = yield path_formatter.traverse(Either.import_path, Either)
        reporter_handler = yield reporter.traverse(Either.import_path, Either)
        syntax_handler = yield syntax.traverse(Either.import_path, Either)
        return ParseHandlers.cons(
            filter_handlers,
            first_error_handler,
            path_formatter_handler,
            reporter_handler,
            syntax_handler,
        )

    @staticmethod
    def cons(
            filter: List[OutputFilter]=Nil,
            first_error: Maybe[FirstError]=Nothing,
            path_formatter: Maybe[PathFormatter]=Nothing,
            reporter: Maybe[Reporter]=Nothing,
            syntax: Maybe[SyntaxCons]=Nothing
    ) -> 'ParseHandlers':
        return ParseHandlers(
            filter,
            first_error.get_or_strict(default_first_error),
            path_formatter.get_or_strict(default_path_formatter),
            reporter.get_or_strict(verbatim_report),
            syntax.get_or_strict(no_syntax),
        )


    def __init__(
            self,
            filter: List[OutputFilter],
            first_error: FirstError,
            path_formatter: PathFormatter,
            reporter: Reporter,
            syntax: SyntaxCons,
    ) -> None:
        self.filter = filter
        self.first_error = first_error
        self.path_formatter = path_formatter
        self.reporter = reporter
        self.syntax = syntax


__all__ = ('ParseHandlers',)
