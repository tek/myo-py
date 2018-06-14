from amino import Dat, Maybe, List, Nil
from amino.tc.monoid import Monoid


class ParseConfig(Dat['ParseConfig']):

    @staticmethod
    def cons(
            langs: List[str]=Nil,
            filter: List[str]=Nil,
            first_error: str=None,
            path_formatter: str=None,
            reporter: str=None,
    ) -> 'ParseConfig':
        return ParseConfig(
            langs,
            filter,
            Maybe.optional(first_error),
            Maybe.optional(path_formatter),
            Maybe.optional(reporter),
        )

    def __init__(
            self,
            langs: List[str],
            filter: List[str],
            first_error: Maybe[str],
            path_formatter: Maybe[str],
            reporter: Maybe[str],
    ) -> None:
        self.langs = langs
        self.filter = filter
        self.first_error = first_error
        self.path_formatter = path_formatter
        self.reporter = reporter


class Monoid_ParseConfig(Monoid, tpe=ParseConfig):

    @property
    def empty(self) -> ParseConfig:
        return ParseConfig.cons()

    def combine(self, a: ParseConfig, b: ParseConfig) -> ParseConfig:
        return ParseConfig(
            a.langs + b.langs,
            a.filter + b.filter,
            a.first_error.o(b.first_error),
            a.path_formatter.o(b.path_formatter),
            a.reporter.o(b.reporter),
        )


class LangConfig(Dat['LangConfig']):

    @staticmethod
    def cons(
            name: str,
            output_filter: List[str]=None,
            output_first_error: str=None,
            output_path_formatter: str=None,
            output_reporter: str=None,
    ) -> 'LangConfig':
        return LangConfig(
            name,
            Maybe.optional(output_filter),
            Maybe.optional(output_first_error),
            Maybe.optional(output_path_formatter),
            Maybe.optional(output_reporter),
        )

    def __init__(
            self,
            name: str,
            output_filter: Maybe[List[str]],
            output_first_error: Maybe[str],
            output_path_formatter: Maybe[str],
            output_reporter: Maybe[str],
    ) -> None:
        self.name = name
        self.output_filter = output_filter
        self.output_first_error = output_first_error
        self.output_path_formatter = output_path_formatter
        self.output_reporter = output_reporter

    @property
    def parse(self) -> ParseConfig:
        return ParseConfig(
            Nil,
            self.output_filter.get_or_strict(Nil),
            self.output_first_error,
            self.output_path_formatter,
            self.output_reporter,
        )


__all__ = ('ParseConfig', 'LangConfig',)
