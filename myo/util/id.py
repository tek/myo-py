from typing import TypeVar

from chiasma.util.id import IdentSpec, Ident, ensure_ident

from ribosome.nvim.io.state import NS
from ribosome.compute.prog import Prog

D = TypeVar('D')


def ensure_ident_ns(spec: IdentSpec) -> NS[D, Ident]:
    return NS.e(ensure_ident(spec))


def ensure_ident_prog(spec: IdentSpec) -> Prog[Ident]:
    return Prog.e(ensure_ident(spec))


__all__ = ('ensure_ident_ns', 'ensure_ident_prog',)
