from typing import Tuple
from functools import singledispatch  # type: ignore

from amino.task import Task
from amino.anon import L
from amino import _, __, Left, F, Right, Empty, Either, Maybe
from amino.lazy import lazy

from ribosome.machine.transition import Fatal

from myo.logging import Logging
from myo.ui.tmux.server import Server
from myo.ui.tmux.layout import Layout
from myo.ui.tmux.pane import Pane, PaneAdapter
from myo.command import ShellCommand
from myo.ui.tmux.view_path import ViewPath
from myo.ui.tmux.view import View


class LayoutFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.server = server
        self.panes = PaneFacade(server)

    def layout_open(self, layout):
        return (layout.layouts.exists(self.layout_open) or
                layout.panes.exists(self.panes.is_open))

    def view_open(self, view):
        f = (self.layout_open if isinstance(view, Layout) else
             self.panes.is_open)
        return f(view)

    is_open = view_open

    def open_views(self, layout):
        return layout.views.filter(self.view_open)

    def ref_pane_fatal(self, layout) -> Task[Pane]:
        ''' A pane in the layout to be used to open a pane.
        Uses the first open pane available.
        Failure if no panes are open.
        '''
        return (Task.call(self._ref_pane, layout) //
                L(Task.from_maybe)(_, "no ref pane for {}".format(layout)))

    def _ref_pane(self, layout) -> Maybe[Pane]:
        return (
            self._opened_panes(layout.panes).sort_by(_.position | 0).last
            .or_else(layout.layouts.find_map(self._ref_pane))
        )

    def open_pane_path(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        ''' legacy version
        '''
        p = path.view
        return (Task.now(Left('pane {} already open'.format(p)))
                if self.panes.is_open(p)
                else self._open_pane_path(path))

    def _open_in_layouts_path(self, pane, layout, outer):
        if self.layout_open(layout):
            return self._open_in_layout(pane, layout) / (_ + (outer,))
        else:
            return (
                outer.detach_last.map2(F(self._open_in_layouts_path, pane)) |
                Task.failed('cannot open {} without open layout'.format(pane))
            ).map3(lambda p, l, o: (p, layout, o.cat(l)))

    def _open_in_layout(self, pane, layout) -> Task[Tuple[Layout, Pane]]:
        return self._split_pane(layout, pane) & (Task.now(layout))

    def close_pane_path(self, path: ViewPath):
        new_path = path.map_view(__.set(id=Empty()))
        return self.panes.close(path.view) / __.replace(new_path)

    def _opened_panes(self, panes):
        return panes.filter(self.panes.is_open)


class PaneFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.server = server

    @lazy
    def panes(self):
        return self.server.panes

    @lazy
    def pane_data(self):
        return self.server.pane_data

    @lazy
    def pane_ids(self):
        return self.pane_data // _.id_i.to_list

    def is_open(self, pane):
        return pane.id.exists(self.pane_ids.contains)

    def find_by_id(self, id):
        return self.panes.find(__.id_i.contains(id))

    def find_by_name(self, name):
        return self.panes.find(_.name == name)

    def select_pane(self, session_id, window_id, pane_id):
        return (
            self.server.session_by_id(session_id) //
            __.window_by_id(window_id) //
            __.pane_by_id(pane_id)
        )

    def find(self, pane: Pane) -> Maybe[PaneAdapter]:
        def find_by_id(pane_id):
            return (
                (pane.session_id & pane.window_id)
                .flat_map2(L(self.select_pane)(_, _, pane_id))
                .or_else(L(self.find_by_id)(pane_id))
            )
        return pane.id // find_by_id

    def run_command(self, pane: Pane, command: ShellCommand):
        return self.run_command_line(pane, command.line)

    def close(self, pane: Pane):
        err = 'cannot close pane {}: not found'.format(pane)
        return (Task.call(self.find, pane) //
                __.cata(__.kill.map(Right), lambda: Task.now(Left(err))))

    def close_id(self, id: int):
        return self.server.cmd('kill-pane', '-t', '%{}'.format(id))

    def pipe(self, pane: Pane, base: str):
        lg = lambda p: self.log.debug(
            'piping {} to {}'.format(p.name, p.log_path | 'nowhere'))
        return (
            self.find(pane)
            .task(Fatal('pipe: pane not found')) /
            __.pipe(base) /
            pane.setter.log_path %
            lg
        )


class ViewFacade(Logging):

    def __init__(self, server: Server) -> None:
        self.layouts = LayoutFacade(server)
        self.panes = PaneFacade(server)

    def _discern(self, view: View):
        return self.layouts if isinstance(view, Layout) else self.panes

    def is_open(self, view: View):
        return self._discern(view).is_open(view)

__all__ = ('LayoutFacade', 'PaneFacade')
