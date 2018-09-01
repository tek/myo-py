from typing import Callable, TypeVar

from amino import List, Either

from ribosome.nvim.io.state import NS

A = TypeVar('A')
D = TypeVar('D')


def resolve_callbacks(paths: List[str]) -> Either[str, List[Callable[..., NS[D, A]]]]:
    return paths.traverse(Either.import_path, Either)


__all__ = ('resolve_callbacks',)
