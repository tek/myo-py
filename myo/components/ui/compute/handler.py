from typing import Callable

from amino import Maybe, Do

from ribosome.compute.api import prog
from ribosome.compute.program import Program
from ribosome.compute.prog import Prog

from chiasma.util.id import Ident

from myo.ui.ui import Ui
from myo.components.ui.compute.pane import view_owners


@prog.do(Program)
def ui_handler(ident: Ident, handler: Callable[[Ui], Maybe[Program]], desc: str) -> Do:
    space, window, owner = yield view_owners(ident)
    yield Prog.m(handler(owner), lambda: f'ui `{type(owner)}` has no handler for `{desc}`')


__all__ = ('ui_handler',)
