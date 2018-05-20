from typing import Callable

from myo.components.tmux.data import TmuxData
from chiasma.data.session import Session
from chiasma.commands.session import session_id
from chiasma.data.window import Window
from chiasma.commands.window import window_id
from chiasma.data.pane import Pane
from chiasma.commands.pane import pane_id

from amino import do, Do, List, Maybe

from ribosome.nvim.io.state import NS
from ribosome.config.component import ComponentData, comp_data
from ribosome.compute.api import prog

from myo.env import Env
from myo.data.info import InfoWidget


def format_id(id: Maybe[int], formatter: Callable[[int], str]) -> str:
    return id.map(lambda a: f' {formatter(a)}') | ''


def format_pane(pane: Pane) -> List[str]:
    return List(f'◳ {pane.ident.str}{format_id(pane.id, pane_id)}')


def format_window(window: Window) -> List[str]:
    return List(f'□ {window.ident.str}{format_id(window.id, window_id)}')


def format_session(session: Session) -> List[str]:
    return List(f'⬚ {session.ident.str}{format_id(session.id, session_id)}')


@prog
@do(NS[ComponentData[Env, TmuxData], InfoWidget])
def tmux_info() -> Do:
    s = yield comp_data()
    views = s.views
    sessions = (views.sessions // format_session).indent(1)
    windows = (views.windows // format_window).indent(1)
    panes = (views.panes // format_pane).indent(1)
    yield NS.pure(InfoWidget.cons(List('Tmux:') + sessions + windows + panes))

__all__ = ('tmux_info',)
