from typing import Callable

import libtmux

from lenses import lens

from amino import List, _, __, Just, Maybe, Map, Right, Empty, Either, Boolean
from amino.lazy import lazy
from amino.task import Task
from amino.anon import L

from ribosome.machine import may_handle, handle, Quit
from ribosome.record import field, list_field, Record
from ribosome.machine.base import DataEitherTask, UnitTask

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.message import (TmuxOpenPane, TmuxRunCommand,
                                      TmuxCreatePane, TmuxCreateLayout,
                                      TmuxCreateSession, TmuxSpawnSession,
                                      TmuxFindVim, TmuxInfo, TmuxLoadDefaults,
                                      TmuxClosePane, TmuxRunShell,
                                      TmuxRunLineInShell, StartWatcher,
                                      WatchCommand, QuitWatcher, SetCommandLog,
                                      TmuxPack)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import LayoutDirections, Layout, VimLayout
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server
from myo.util import parse_int, view_params
from myo.ui.tmux.window import VimWindow, Window
from myo.ui.tmux.facade import LayoutFacade, PaneFacade
from myo.ui.tmux.view import View
from myo.plugins.core.message import AddDispatcher
from myo.plugins.tmux.dispatch import TmuxDispatcher
from myo.ui.tmux.util import format_state, Ident
from myo.ui.tmux.pane_path import PanePathMod, ppm_id
from myo.plugins.command.message import SetShellTarget
from myo.command import Command, Shell
from myo.plugins.tmux.watcher import Watcher, Terminated

_is_vim_window = lambda a: isinstance(a, VimWindow)
_is_vim_layout = lambda a: isinstance(a, VimLayout)
_is_vim_pane = lambda a: isinstance(a, VimPane)


def _ident_ppm(ident: Ident):
    return PanePathMod(pred=__.has_ident(ident))


class TmuxState(Record):
    server = field(Server)
    sessions = list_field()
    windows = list_field()
    instance_id = field(str, initial='', factory=L(List.random_string)(5))

    @property
    def vim_window(self):
        return self.windows.find(_is_vim_window)

    @property
    def vim_window_lens(self):
        return (self.windows.find_lens_pred(_is_vim_window) /
                lens(self).windows.add_lens)

    @property
    def vim_layout(self):
        return self.vim_window // __.root.layouts.find(_is_vim_layout)

    @property
    def vim_layout_lens(self):
        return (
            self.vim_layout //
            __.layouts.find_lens_pred(_is_vim_layout) /
            lens(self).windows.add_lens
        )

    @property
    def vim_pane(self):
        return self.vim_layout / _.panes / _.head

    @property
    def all_panes(self):
        return self.windows // _.root.all_panes

    def pane(self, ident):
        return self.all_panes.find(__.has_ident(ident))

    @property
    def possibly_open_panes(self):
        return (
            self.all_panes
            .filter(_.id.is_just)
            .filter(lambda a: not _is_vim_pane(a))
        )


class TmuxTransitions(MyoTransitions):

    def _state(self, data):
        return data.sub_state(self.name, self.machine.new_state)

    @property
    def state(self):
        return self._state(self.data)

    def _with_sub(self, data, state):
        return data.with_sub_state(self.name, state)

    def with_sub(self, state):
        return self._with_sub(self.data, state)

    def _with_root(self, data, state, root):
        l = state.vim_window_lens / _.root
        new_state = l / __.set(root) | state
        return self._with_sub(data, new_state)

    def _with_vim_window(self, data, state, win):
        new_state = state.vim_window_lens / __.set(win) | state
        return self._with_sub(data, new_state)

    def with_sub_and_msgs(self, state, msgs):
        return (self.with_sub(state),) + msgs

    @property
    def server(self):
        return self.state.server

    @property
    def layouts(self):
        return self.machine.layouts

    @property
    def panes(self):
        return self.machine.panes

    @may_handle(StageI)
    def stage_1(self):
        ''' Initialize the state. If it doesn't exist, Env will create
        it using the constructor function supplied in *Plugin.state*
        '''
        default = self.pflags.tmux_use_defaults.maybe(TmuxLoadDefaults())
        msgs = List(AddDispatcher(), self.with_sub(self.state), TmuxFindVim())
        return msgs + default.to_list + List(StartWatcher())

    @may_handle(AddDispatcher)
    def add_dispatcher(self):
        return self.data + TmuxDispatcher()

    @may_handle(TmuxFindVim)
    def find_vim(self):
        vim_pid = self._vim_pid
        vim_pane = vim_pid // self._find_vim_pane
        id = (
            (self.vim.pvar('tmux_force_vim_pane_id') // parse_int)
            .or_else(vim_pane // _.id_i)
        )
        wid = (
            self.vim.pvar('tmux_force_vim_win_id')
            .or_else(vim_pane // _.window_id_i)
            .to_either('no vim win id')
        )
        sid = (
            self.vim.pvar('tmux_force_vim_session_id')
            .or_else(vim_pane // _.session_id_i)
            .to_either('no vim session id')
        )
        vim_w = self.vim.pvar('tmux_vim_width').or_else(Just(85))
        pane = VimPane(id=id.to_maybe, name='vim', pid=vim_pid.to_maybe,
                       window_id=wid, session_id=sid)
        vim_layout = VimLayout(name='vim',
                               direction=LayoutDirections.vertical,
                               panes=List(pane), fixed_size=vim_w)
        root = Layout(name='root',
                      direction=LayoutDirections.horizontal,
                      layouts=List(vim_layout))
        win = VimWindow(id=wid.to_maybe, root=root)
        new_state = self.state.append1.windows(win)
        return self.with_sub(new_state)

    @may_handle(TmuxLoadDefaults)
    def load_defaults(self):
        main = TmuxCreateLayout('main', options=Map(parent='root'))
        make = TmuxCreatePane('make', options=Map(parent='main'))
        return main, make

    @may_handle(StartWatcher)
    def start_watcher(self):
        return UnitTask(Task(self.machine.watcher.start))

    @handle(TmuxCreateSession)
    def create_session(self):
        return (
            self.msg.options.get('name') /
            (lambda n: Session(id=n)) /
            List /
            self.state.append.sessions /
            self.with_sub
        )

    @may_handle(TmuxSpawnSession)
    def spawn_session(self):
        s = self.state.session(self.msg.id)
        self.server.new_session(session_name=s.x)

    @handle(TmuxCreateLayout)
    def create_layout(self):
        opts = self.msg.options
        dir_s = opts.get('direction') | 'vertical'
        direction = LayoutDirections.parse(dir_s)
        layout = Layout(name=self.msg.name, direction=direction,
                        **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.layouts, layout)

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        pane = Pane(name=self.msg.name, **view_params(opts))
        return self._add_to_layout(opts.get('parent'), _.panes, pane)

    @may_handle(TmuxOpenPane)
    def open(self):
        return self._open_pane_ppm(self.msg.name)

    @may_handle(TmuxClosePane)
    def close(self):
        return self._close_pane_ppm(self.msg.name)

    @may_handle(TmuxRunCommand)
    def run_command(self):
        command = self.msg.command
        shell = command.shell // self.data.shell
        options = self.msg.options
        return shell.cata(
            L(self._run_in_shell)(command, _, options),
            L(self._run_command)(command, options)
        )

    @may_handle(TmuxRunShell)
    def run_shell(self):
        shell = self.msg.shell
        default = Map(shell.target.map(lambda a: ('pane', a)).to_list)
        opts = default ** self.msg.options
        return TmuxRunCommand(command=shell, options=opts)

    @handle(SetShellTarget)
    def set_shell_target(self):
        target = self._pane(self.msg.target) / _.uuid
        setter = __.modify(__.set(target=target))
        return (self.data.command_lens(self.msg.shell.uuid)).map(setter)

    @handle(TmuxRunLineInShell)
    def run_line_in_shell(self):
        opt = self.msg.options
        return (
            opt.get('line') /
            (lambda a: Command(name='temp', line=a)) /
            L(self._run_in_shell)(_, self.msg.shell, opt)
        )

    @may_handle(PanePathMod)
    def pane_path_mod(self):
        return self._run_ppm(self.msg)

    @may_handle(Quit)
    def quit(self):
        t = self.state.possibly_open_panes // _.id / self.panes.close_id
        return QuitWatcher(), UnitTask(t.sequence(Task))

    @may_handle(QuitWatcher)
    def quit_watcher(self):
        return UnitTask(Task(self.machine.watcher.stop))

    @may_handle(TmuxInfo)
    def info(self):
        self.log.info('\n'.join(format_state(self.state)))

    @may_handle(Terminated)
    def terminated(self):
        return self._pane_mod(self.msg.pane.uuid, __.setter.pid(Empty()))

    @may_handle(SetCommandLog)
    def set_command_log(self):
        def set_log(data):
            log_path = self._pane(self.msg.pane_ident) // _.log_path
            cmd = data.command_lens(self.msg.cmd_ident)
            res = cmd / (lambda c: c.modify(__.set(log_path=log_path)))
            return res.to_either('command not found')
        # NOTE Must run this as a task so it is executed after the cmd runner
        return DataEitherTask(_ / set_log)

    @may_handle(TmuxPack)
    def pack(self):
        return self._window_task(self.layouts.pack_window)

    def _window_task(self, f: Callable[[Window], Task[Either[str, Window]]]):
        return DataEitherTask(_ // L(self._wrap_window)(_, f))

    def _wrap_window(self, data, callback):
        state = self._state(data)
        win = Task.from_maybe(state.vim_window, 'no vim window')
        update = __.map(L(self._with_vim_window)(data, state, _))
        return win // callback / update

    def _run_ppm(self, ppm):
        return self._window_task(ppm.run)

    def _open_pane_ppm(self, name: Ident):
        # cannot reference self.layouts.pack_path directly, because panes
        # are cached
        return _ident_ppm(name) / self._open_pane / self._pack_path

    def _close_pane_ppm(self, name: Ident):
        return _ident_ppm(name) / self._close_pane / self._pack_path

    def _run_command_ppm(self, command, opt: Map):
        in_shell = Boolean('shell' in opt)
        pane_ident = opt.get('pane') | self._default_pane_name
        def check_running(path):
            return Task.now(Right(path)) if in_shell else (
                self.panes.ensure_not_running(path.pane) /
                __.replace(path)
            )
        def pipe(path):
            return (
                self.panes.pipe(path.pane, self.state.instance_id) /
                path.setter.pane /
                Right
            )
        def run(path):
            return (
                self._run_command_line(command.line, path.pane, opt) /
                (lambda a: Right(path))
            )
        def pid(path):
            return (
                self.panes.command_pid(path.pane) /
                (lambda a: path.map_pane(__.set(pid=a))) /
                Right
            )
        def watch(path):
            msg = WatchCommand(command, path.pane)
            return (
                Task.call(self.machine.watcher.send, msg)
                .replace(Right(path))
            )
        runner = (
            (self._open_pane_ppm(pane_ident) + check_running) /
            in_shell.no.maybe(pipe).get_or_else(lambda: ppm_id) /
            run /
            pid /
            watch
        )
        set_log = command.transient.no.maybe(
            SetCommandLog(command.uuid, pane_ident))
        return set_log.to_list.cons(runner)

    def _open_pane(self, w):
        return self.layouts.open_pane(w)

    def _close_pane(self, w):
        return self.layouts.close_pane_path(w)

    def _pack_path(self, path):
        return self.layouts.pack_path(path)

    def _layout_lens_bound(self, name):
        def sub(a):
            return a.layouts.find_lens(ll) / lens().layouts.add_lens
        def ll(l):
            return Just(lens()) if l.name == name else sub(l)
        return (
            self.state.windows
            .find_lens(lambda a: ll(a.root) / lens().root.add_lens) /
            lens(self.state).windows.add_lens
        )

    def _add_to_layout(self, parent: Maybe[str], target: Callable, view: View):
        name = parent | 'root'
        return (
            self._layout_lens_bound(name) /
            target /
            __.modify(__.cat(view)) /
            self.with_sub
        )

    def _pane(self, ident: Ident):
        return self.state.vim_window // __.root.find_pane(ident)

    def _pane_uuid(self, ident: Ident):
        return self._pane(ident) / _.uuid

    def _default_pane_name(self):
        return 'make'

    def _pane_mod(self, ident: Ident, f: Callable[[Pane], Pane]):
        def g(path):
            return Task.now(Right(path.map_pane(f)))
        return _ident_ppm(ident) / g

    @property
    def _vim_pid(self):
        return self.vim.call('getpid').to_either('no pid')

    def _find_vim_pane(self, vim_pid):
        return self.server.pane_data.find(__.command_pid.contains(vim_pid))

    def _run_command_line(self, line, pane, options):
        return self.panes.run_command_line(pane, line)

    def _run_command(self, command, options):
        return self._run_command_ppm(command, options)

    def _run_in_shell(self, command: Command, shell: Shell, options: Map):
        ident = shell.target | self._default_pane_name
        opt = options + ('pane', ident) + ('shell', shell)
        cmd_runner = self._run_command(command, opt)
        shell_runner = TmuxRunShell(shell, Map())
        return cmd_runner.cons(shell_runner)


class Plugin(MyoComponent):

    Transitions = TmuxTransitions

    @lazy
    def native_server(self):
        socket = self.vim.pvar('tmux_socket') | None
        return libtmux.Server(socket_name=socket)

    @property
    def server(self):
        return Server(self.native_server)

    @property
    def layouts(self):
        return LayoutFacade(self.server)

    @property
    def panes(self):
        return PaneFacade(self.server)

    def new_state(self):
        return TmuxState(server=self.server)

    @lazy
    def watcher(self):
        interval = self.vim.pvar('tmux_watcher_interval') | 1.0
        return Watcher(self, interval=interval)

__all__ = ('Plugin',)
