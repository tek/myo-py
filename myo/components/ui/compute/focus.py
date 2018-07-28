from amino import Do

from ribosome.compute.api import prog

from chiasma.util.id import IdentSpec

from myo.util.id import ensure_ident_prog
from myo.components.ui.compute.pane import view_prog


@prog.do(None)
def focus(ident_spec: IdentSpec) -> Do:
    ident = yield ensure_ident_prog(ident_spec)
    handler = yield view_prog(ident, lambda a: a.focus_pane, 'focus_pane')
    yield handler(ident)


__all__ = ('focus',)
