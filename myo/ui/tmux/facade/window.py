import time
import signal
from typing import Tuple

from psutil import Process

from amino import (L, Task, _, Maybe, F, __, Either, I, Right, Left, List,
                   Empty, Try)
from amino.lazy import lazy
from amino.task import task

from ribosome.machine.transition import Fatal, NothingToDo
from ribosome.machine.state import Info

from myo.logging import Logging
from myo.ui.tmux.session import Session
from myo.ui.tmux.window import Window, WindowAdapter
from myo.ui.tmux.pane import Pane, PaneAdapter
from myo.ui.tmux.view_path import ViewPath
from myo.ui.tmux.layout import Layout
from myo.command import ShellCommand
from myo.ui.tmux.view import View


pane_not_found_error = 'pane not found: {}'


class WindowFacade(Logging):

    def __init__(self, session: Session, window: Window, adapter:
                 WindowAdapter) -> None:
        self.session = session
        self.window = window
        self.adapter = adapter

    @property
    def window_size(self):
        return self.adapter.size

    @lazy
    def panes(self):
        return self.adapter.panes

    @property
    def root(self):
        return self.window.root

    def ref_pane_fatal(self, layout: Layout) -> Task[Pane]:
        ''' A pane in the layout to be used to open a pane.
        Uses the first open pane available.
        Failure if no panes are open.
        '''
        return (Task.call(self._ref_pane, layout) //
                L(Task.from_maybe)(_, "no ref pane for {}".format(layout)))

    def _ref_pane(self, layout: Layout) -> Maybe[Pane]:
        return (
            self._opened_panes(layout.panes).sort_by(_.position | 0).last
            .o(layout.layouts.find_map(self._ref_pane))
        )

    def native_ref_pane(self, layout: Layout):
        return self.ref_pane_fatal(layout) // self.native_pane_task_fatal

    def native_pane(self, pane: Pane):
        return ((pane.id // self.adapter.pane_by_id)
                .to_either((pane_not_found_error.format(pane.name))))

    def native_pane_task(self, pane: Pane):
        return Task.call(self.native_pane, pane)

    def native_pane_task_fatal(self, pane: Pane):
        return self.native_pane_task(pane).join_either

    def open_pane(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        v = path.view
        def open(pane):
            def apply(layout):
                set = path.is_pane.c(lambda: I, lambda: v.replace_pane)
                return (
                    self._split_pane(layout, pane) /
                    set /
                    path.setter.view /
                    Right
                )
            return (self._pane_opener(path, pane).eff(Either) // apply).value
        view = (Task.now(v) if path.is_pane else
                v.panes.head.task('{} has no panes'.format(v)))
        return view // open

    def _pane_opener(self, path: ViewPath, pane: Pane
                     ) -> Task[Either[str, Layout]]:
        def find_layout():
            return (path.layouts.reversed
                    .find(self.layout_open)
                    .to_either(
                        Fatal('no open layout when trying to open pane')))
        return Task.now(
            self.view_open(pane).no.flat_either_call(
                Left(NothingToDo('{!r} already open'.format(pane))),
                find_layout,
            )
        )

    def _split_pane(self, layout, pane) -> Task[Pane]:
        return (
            self.native_ref_pane(layout) /
            __.split(layout.horizontal) /
            PaneAdapter /
            pane.open
        )

    def pack_path(self, path: ViewPath):
        return self.pack / __.replace(path)

    @property
    def pack(self):
        from myo.ui.tmux.pack import WindowPacker
        return WindowPacker(self).run

    def run_command_line(self, pane: Pane, line: str):
        return (
            self.native_pane_task_fatal(pane) /
            __.run_command(line)
        )

    def ensure_not_running(self, pane: Pane, kill=False, signals=List('kill')):
        def handle(pa):
            return (
                Task.now(Right(True))
                if pa.not_running else
                self._kill_process(pa, signals=signals)
                if pane.kill or kill else
                Task.now(Left('command already running'))
            )
        return self.native_pane_task_fatal(pane) // handle

    def command_pid(self, pane: Pane):
        return self.native_pane_task_fatal(pane) / _.command_pid

    def kill_process(self, pane, signals):
        return (self.native_pane_task_fatal(pane) //
                L(self._kill_process)(_, signals))

    @task
    def _kill_process(self, adapter, signals):
        def _wait_killed(timeout):
            start = time.time()
            while time.time() - start > timeout and adapter.running:
                time.sleep(.1)
        def kill(signame):
            if adapter.running:
                sig = getattr(signal, 'SIG{}'.format(signame.upper()),
                              signal.SIGINT)
                (
                    adapter.command_pid //
                    L(Try)(Process, _) //
                    L(Try)(__.send_signal, sig)
                )
                _wait_killed(3)
            return adapter.not_running
        return (
            signals.find(kill) /
            'process killed by signal {}'.format /
            Info /
            Right |
            Left(Fatal('could not kill running process'))
        )

    def pipe(self, pane: Pane, base: str):
        lg = lambda p: self.log.debug(
            'piping {} to {}'.format(p.name, p.log_path | 'nowhere'))
        return (
            self.native_pane_task_fatal(pane) /
            __.pipe(base) /
            pane.setter.log_path %
            lg
        )

    @property
    def pane_ids(self):
        return self.panes // _.id_i

    def pane_open(self, pane: Pane):
        return pane.id.exists(self.pane_ids.contains)

    def layout_open(self, layout: Layout):
        return (layout.panes.exists(self.pane_open) or
                layout.layouts.exists(self.layout_open))

    def view_open(self, view: View):
        f = self.layout_open if isinstance(view, Layout) else self.pane_open
        return f(view)

    is_open = view_open

    def open_views(self, layout: Layout):
        return layout.views.filter(self.view_open)

    def open_pane_path(self, path: ViewPath) -> Task[Either[str, ViewPath]]:
        ''' legacy version
        '''
        p = path.view
        return (Task.now(Left('pane {} already open'.format(p)))
                if self.is_open(p)
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
        return self.close(path.view) / __.lmap(Fatal).replace(new_path)

    def _opened_panes(self, panes):
        return panes.filter(self.is_open)

    def run_command(self, pane: Pane, command: ShellCommand):
        return self.run_command_line(pane, command.line)

    def close(self, pane: Pane):
        return (self.native_pane_task(pane).eff(Either) //
                __.kill.map(Right)).value

    def focus(self, pane: Pane):
        return (
            self.native_pane(pane)
            .task('pane not found for focus: {}'.format(pane)) /
            __.focus()
        )

__all__ = ('WindowFacade',)
