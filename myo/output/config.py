from amino import Dat, Maybe, List

from chiasma.util.id import IdentSpec, ensure_ident_or_generate, Ident


class LangConfig(Dat['LangConfig']):

    @staticmethod
    def cons(
            ident: IdentSpec=None,
            output_filter: List[str]=None,
            output_first_error: str=None,
            output_path_truncator: str=None,
    ) -> 'LangConfig':
        return LangConfig(
            ensure_ident_or_generate(ident),
            Maybe.optional(output_filter),
            Maybe.optional(output_first_error),
            Maybe.optional(output_path_truncator),
        )

    def __init__(
            self,
            ident: Ident,
            output_filter: Maybe[List[str]],
            output_first_error: Maybe[str],
            output_path_truncator: Maybe[str],
    ) -> None:
        self.ident = ident
        self.output_filter = output_filter
        self.output_first_error = output_first_error
        self.output_path_truncator = output_path_truncator


__all__ = ('LangConfig',)
