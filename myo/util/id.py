from typing import TypeVar

from chiasma.util.id import IdentSpec, Ident, ensure_ident

from ribosome.nvim.io.state import NS

D = TypeVar('D')


def ensure_ident_ns(spec: IdentSpec) -> NS[D, Ident]:
    return NS.e(ensure_ident(spec))


__all__ = ('ensure_ident_ns',)
