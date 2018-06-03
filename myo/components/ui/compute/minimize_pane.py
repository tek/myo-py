from typing import Union

from amino import do, Do

from chiasma.util.id import ensure_ident_or_generate
from amino.boolean import true
from amino.state import EitherState
from amino.lenses.lens import lens

from ribosome.compute.api import prog
from ribosome.config.component import ComponentData
from ribosome.compute.prog import Prog

from myo.util import Ident
from myo.ui.data.ui_data import UiData
from myo.ui.data.window import Window
from myo.env import Env
from myo.ui.pane import ui_modify_pane
from myo.components.ui.compute.pane import render_view


@do(EitherState[UiData, Window])
def ui_minimize_pane(ident: Ident) -> Do:
    yield ui_modify_pane(ident, lens.state.minimized.set(true))


@prog
@do(EitherState[ComponentData[Env, UiData], Window])
def ui_minimize_pane_prog(ident: Ident) -> Do:
    yield ui_minimize_pane(ident).zoom(lens.comp)


@prog.do(None)
def minimize_pane(ident_spec: Union[str, Ident]) -> Do:
    ident = ensure_ident_or_generate(ident_spec)
    yield ui_minimize_pane_prog(ident)
    yield render_view(ident)


__all__ = ('minimize_pane',)
