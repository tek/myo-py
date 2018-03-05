from amino import do, Do, Dat, Maybe, Nothing, _
from amino.state import EitherState
from amino.lenses.lens import lens

from chiasma.util.id import Ident
from chiasma.ui.view_geometry import ViewGeometry

from ribosome.trans.api import trans
from ribosome.dispatch.component import ComponentData
from ribosome import ribo_log

from myo.env import Env
from myo.ui.data.ui_data import UiData
from myo.ui.data.view import Pane
from myo.ui.pane import insert_pane_into_ui


class CreatePaneOptions(Dat['CreatePaneOptions']):

    @staticmethod
    def cons(
            layout: Ident,
            name: Maybe[Ident]=Nothing,
            min_size: Maybe[int]=Nothing,
            max_size: Maybe[int]=Nothing,
            fixed_size: Maybe[int]=Nothing,
            minimized_size: Maybe[int]=Nothing,
            weight: Maybe[float]=Nothing,
            position: Maybe[int]=Nothing,
    ) -> 'CreatePaneOptions':
        return CreatePaneOptions(
            layout,
            name,
            min_size,
            max_size,
            fixed_size,
            minimized_size,
            weight,
            position,
        )

    def __init__(
            self,
            layout: Ident,
            name: Maybe[Ident],
            min_size: Maybe[int],
            max_size: Maybe[int],
            fixed_size: Maybe[int],
            minimized_size: Maybe[int],
            weight: Maybe[float],
            position: Maybe[int],
    ) -> None:
        self.layout = layout
        self.name = name
        self.min_size = min_size
        self.max_size = max_size
        self.fixed_size = fixed_size
        self.minimized_size = minimized_size
        self.weight = weight
        self.position = position


def pane_from_options(options: CreatePaneOptions) -> Pane:
    return Pane.cons(
        ident=options.name | Ident.generate,
        geometry=ViewGeometry(
            options.min_size,
            options.max_size,
            options.fixed_size,
            options.minimized_size,
            options.weight,
            options.position,
        )
    )


@trans.free.unit(trans.st)
@do(EitherState[ComponentData[Env, UiData], None])
def create_pane(options: CreatePaneOptions) -> Do:
    pane = pane_from_options(options)
    yield EitherState.modify_f(insert_pane_into_ui(pane, options.layout)).zoom(lens.comp)


__all__ = ('create_pane',)
