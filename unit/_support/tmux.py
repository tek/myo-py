from ribosome.test.integration.run import DispatchHelper

from chiasma.data.view_tree import ViewTree
from chiasma.data.session import Session
from chiasma.data.window import Window as TWindow

from amino import List, __

from myo.ui.data.view import Layout, Pane
from myo.ui.data.window import Window
from myo.ui.data.space import Space


def init_tmux_data(helper: DispatchHelper, layout: ViewTree[Layout, Pane]) -> DispatchHelper:
    window = Window.cons('win', layout=layout)
    space = Space.cons('spc', List(window))
    return (
        window,
        space,
        helper
        .mod.state(
            __
            .modify_component_data('ui', __.append1.spaces(space))
            .modify_component_data(
                'tmux',
                __
                .append1.sessions(Session.cons(space.ident, id=0))
                .append1.windows(TWindow.cons(window.ident, id=0))
            )
        )
    )


__all__ = ('init_tmux_data',)
