from amino import Do

from chiasma.util.id import IdentSpec, ensure_ident_or_generate

from ribosome.compute.api import prog
from ribosome.compute.prog import Prog

from myo.components.ui.compute.pane import view_owners
from myo.util.id import ensure_ident_prog


@prog.do(None)
def kill_pane(ident_spec: IdentSpec) -> Do:
    ident = yield ensure_ident_prog(ident_spec)
    space, window, owner = yield view_owners(ident)
    kill_handler = yield Prog.m(owner.kill_pane, lambda: f'ui `{type(owner)}` has no handler for `kill_pane`')
    yield kill_handler(ident)


__all__ = ('kill_pane',)
