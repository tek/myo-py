from typing import Callable

from lenses import lens

from amino import (List, _, __, Just, Maybe, Map, Right, Empty, Either,
                   Boolean, I)
from amino.lazy import lazy
from amino.task import Task
from amino.anon import L

from ribosome.machine import may_handle, handle, Quit, Nop
from ribosome.record import field, list_field, Record
from ribosome.machine.base import UnitTask, DataTask

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.message import (TmuxOpen, TmuxRunCommand, TmuxCreatePane,
                                      TmuxCreateLayout, TmuxCreateSession,
                                      TmuxSpawnSession, TmuxFindVim, TmuxInfo,
                                      TmuxLoadDefaults, TmuxClosePane,
                                      TmuxRunShell, TmuxRunLineInShell,
                                      StartWatcher, WatchCommand, QuitWatcher,
                                      SetCommandLog, TmuxPack, TmuxPostOpen,
                                      TmuxFixFocus, TmuxMinimize, TmuxRestore,
                                      TmuxToggle, TmuxFocus, TmuxOpenOrToggle,
                                      TmuxKill)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane
from myo.ui.tmux.layout import LayoutDirections, Layout, VimLayout
from myo.ui.tmux.session import Session
from myo.ui.tmux.server import Server, NativeServer
from myo.util import parse_int
from myo.ui.tmux.window import VimWindow, Window
from myo.ui.tmux.facade import LayoutFacade, PaneFacade, ViewFacade
from myo.ui.tmux.view import View
from myo.plugins.core.message import AddDispatcher
from myo.plugins.tmux.dispatch import TmuxDispatcher
from myo.ui.tmux.util import format_state, Ident
from myo.ui.tmux.view_path import LayoutPathMod, PanePathMod, ViewPathMod
from myo.plugins.command.message import SetShellTarget
from myo.command import Command, Shell, default_signals
from myo.plugins.tmux.watcher import Watcher, Terminated

_is_vim_window = lambda a: isinstance(a, VimWindow)
_is_vim_layout = lambda a: isinstance(a, VimLayout)
_is_vim_pane = lambda a: isinstance(a, VimPane)


def _ident_ppm(ident: Ident):
    return PanePathMod(pred=__.has_ident(ident))


def _ident_lpm(ident: Ident):
    return LayoutPathMod(pred=__.has_ident(ident))


def _ident_vpm(ident: Ident):
    return ViewPathMod(pred=__.has_ident(ident))


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

    def find_view(self, view: View):
        return self.windows.find_map(__.root.find_view(view))


class TmuxTransitions(MyoTransitions):

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
    def views(self):
        return self.machine.views

    @property
    def panes(self):
        return self.machine.panes

    def record_lens(self, tpe, name):
        return (
            self._pane_lens(name)
            if tpe == 'pane' else
            self._layout_lens(name)
            if tpe == 'layout' else
            Empty()
        )

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
            (self.vim.vars.p('tmux_force_vim_pane_id') // parse_int)
            .or_else(vim_pane // _.id_i)
        )
        wid = (
            self.vim.vars.p('tmux_force_vim_win_id')
            .or_else(vim_pane // _.window_id_i)
            .to_either('no vim win id')
        )
        sid = (
            self.vim.vars.p('tmux_force_vim_session_id')
            .or_else(vim_pane // _.session_id_i)
            .to_either('no vim session id')
        )
        vim_w = self.vim.vars.p('tmux_vim_width').or_else(Just(88))
        pane = VimPane(id=id.to_maybe, name='vim', pid=vim_pid.to_maybe,
                       window_id=wid, session_id=sid)
        vim_layout = VimLayout(name='vim',
                               direction=LayoutDirections.vertical,
                               panes=List(pane), min_size=vim_w,
                               weight=Just(0.0001))
        root = Layout(name='root',
                      direction=LayoutDirections.horizontal,
                      layouts=List(vim_layout))
        win = VimWindow(id=wid.to_maybe, root=root)
        new_state = self.state.append1.windows(win)
        return self.with_sub(new_state)

    @may_handle(TmuxLoadDefaults)
    def load_defaults(self):
        main = TmuxCreateLayout('main',
                                options=Map(parent='root', weight=1))
        make = TmuxCreatePane('make', options=Map(parent='main', pin=True,
                                                  position=-1))
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
        return (
            self._from_opt(Layout, name=self.msg.name, direction=direction) //
            L(self._add_layout_to_layout)(opts.get('parent'), _)
        )

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        return (
            self._from_opt(Pane, name=self.msg.name) //
            L(self._add_pane_to_layout)(opts.get('parent'), _)
        )

    @may_handle(TmuxOpen)
    def open(self):
        name = self.msg.name
        opt = self.msg.options
        pinned = opt.get('pinned').exists(I)
        return (
            self._open_pane_ppm(name),
            (Nop() if pinned else TmuxPostOpen(name, opt - 'pinned'))
        )

    @handle(TmuxPostOpen)
    def open_pinned(self):
        def go(pane):
            return (
                self._pinned_panes(self.msg.ident) /
                L(TmuxOpen)(_, Map(pinned=True))
            ) + List(TmuxFixFocus(pane.ident), TmuxPack().pub.at(1))
        return self._pane(self.msg.ident) / go

    @handle(TmuxFixFocus)
    def fix_focus(self):
        return (
            self._pane(self.msg.pane) // (
                lambda a:
                a.focus.cata(Just(a), self._vim_pane) //
                self._focus_pane
            )
        )

    @handle(TmuxFocus)
    def focus(self):
        return self._pane(self.msg.pane) // self._focus_pane

    def _focus_pane(self, pane: Pane):
        return self.panes.find(pane) / _.focus / Task / UnitTask

    @may_handle(TmuxClosePane)
    def close(self):
        return self._close_pane_ppm(self.msg.name)

    @may_handle(TmuxRunCommand)
    def run_command(self):
        command = self.msg.command
        options = self.msg.options
        shell = options.get('shell').or_else(command.shell) // self.data.shell
        return shell.cata(
            L(self._run_in_shell)(command, _, options),
            L(self._run_command)(command, options)
        )

    @may_handle(TmuxRunShell)
    def run_shell(self):
        shell = self.msg.shell
        default = Map(shell.target.map(lambda a: ('target', a)).to_list)
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
            opt.get('target') /
            (lambda a: Command(name='temp', line=a)) /
            L(self._run_in_shell)(_, self.msg.shell, opt)
        )

    @may_handle(ViewPathMod)
    def view_path_mod(self):
        return self._run_vpm(self.msg)

    @may_handle(PanePathMod)
    def pane_path_mod(self):
        return self._run_vpm(self.msg)

    @may_handle(LayoutPathMod)
    def layout_path_mod(self):
        return self._run_vpm(self.msg)

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

    @handle(SetCommandLog)
    def set_command_log(self):
        def set_log(cmd):
            log = lambda p: self.log.debug(
                'setting {} log to {}'.format(cmd.name, p))
            cmd_lens = self.data.command_lens(cmd.ident)
            log_path = self._pane(self.msg.pane_ident) // _.log_path
            log_path % log
            return cmd_lens / __.modify(__.set(log_path=log_path))
        return self._main_command(self.msg.cmd_ident) // set_log

    @may_handle(TmuxPack)
    def pack(self):
        return self._window_task(self.layouts.pack_window)

    @may_handle(TmuxMinimize)
    def minimize(self):
        return self._minimize(__.set(minimized=True))

    @may_handle(TmuxRestore)
    def restore(self):
        return self._minimize(__.set(minimized=False))

    @may_handle(TmuxToggle)
    def toggle(self):
        return self._minimize(lambda a: a.set(minimized=not a.minimized))

    @handle(TmuxOpenOrToggle)
    def open_or_toggle(self):
        name = self.msg.pane
        return (
            self._view(name) /
            self.views.is_open /
            __.cata(TmuxToggle(name), TmuxOpen(name))
        )

    @handle(TmuxKill)
    def kill(self):
        signals = self.msg.options.get('signals') | default_signals
        return (self._pane(self.msg.pane) //
                L(self.panes.kill_process)(_, signals))

    def _minimize(self, f):
        return self._view_mod(self.msg.pane, f), TmuxPack().pub.at(1)

    def _window_task(self, f: Callable[[Window], Task[Either[str, Window]]]):
        return DataTask(_ // L(self._wrap_window)(_, f))

    def _wrap_window(self, data, callback):
        state = self._state(data)
        win = Task.from_maybe(state.vim_window, 'no vim window')
        update = __.map(L(self._with_vim_window)(data, state, _))
        return win // callback / update

    def _run_vpm(self, vpm):
        return self._window_task(vpm.run)

    def _open_pane_ppm(self, name: Ident):
        # cannot reference self.layouts.pack_path directly, because panes
        # are cached
        return _ident_vpm(name) / self._open_pane

    def _close_pane_ppm(self, name: Ident):
        return _ident_ppm(name) / self._close_pane / self._pack_path

    def _run_command_ppm(self, command, opt: Map):
        in_shell = Boolean('shell' in opt)
        pane_ident = opt.get('target') | self._default_pane_name
        kill = opt.get('kill') | command.kill
        signals = opt.get('signals') / List.wrap | command.signals
        def check_running(path):
            pane_kill = path.view.kill
            return Task.now(Right(path)) if in_shell else (
                self.panes.ensure_not_running(
                    path.view, kill=kill or pane_kill, signals=signals) /
                __.replace(path)
            )
        def pipe(path):
            return (
                self.panes.pipe(path.view, self.state.instance_id) /
                path.setter.view /
                Right
            )
        def run(path):
            return (
                self._run_command_line(command.line, path.view, opt) /
                (lambda a: Right(path))
            )
        def pid(path):
            return (
                self.panes.command_pid(path.view) /
                (lambda a: path.map_view(__.set(pid=a))) /
                Right
            )
        def watch(path):
            msg = WatchCommand(command, path.view)
            return (
                Task.call(self.machine.watcher.send, msg)
                .replace(Right(path))
            )
        runner = (
            (self._open_pane_ppm(pane_ident) + check_running) /
            pipe /
            run /
            pid /
            watch
        )
        set_log = command.transient.no.maybe(
            SetCommandLog(command.uuid, pane_ident))
        return set_log.to_list.cons(runner).cat(TmuxPostOpen(pane_ident, opt))

    def _open_pane(self, path):
        return self.layouts.open_pane(path)

    def _close_pane(self, w):
        return self.layouts.close_pane_path(w)

    def _pack_path(self, path):
        return self.layouts.pack_path(path)

    def _pane_lens(self, ident):
        return self._view_lens(ident, __.pane_lens)

    def _layout_lens(self, ident):
        return self._view_lens(ident, __.layout_lens)

    def _view_lens(self, ident, lens_cb):
        return (
            self.state.windows
            .find_lens(lens_cb(__.has_ident(ident))) /
            lens(self.state).windows.add_lens
        )

    def _layout_lens_bound(self, ident):
        ll = lambda l: Just(lens()) if l.has_ident(ident) else sub(l)
        sub = __.layouts.find_lens(ll).map(lens().layouts.add_lens)
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

    def _add_pane_to_layout(self, parent: Maybe[str], pane: Pane):
        return self._add_to_layout(parent, _.panes, pane)

    def _add_layout_to_layout(self, parent: Maybe[str], layout: Layout):
        return self._add_to_layout(parent, _.layouts, layout)

    def _pane(self, ident: Ident):
        return self.state.pane(ident)

    def _view(self, ident: Ident):
        return self.state.find_view(ident)

    @property
    def _vim_pane(self):
        return self._pane('vim')

    def _pane_uuid(self, ident: Ident):
        return self._pane(ident) / _.uuid

    def _default_pane_name(self):
        return 'make'

    def _pane_mod(self, ident: Ident, f: Callable[[Pane], Pane]):
        return self._mod(_ident_ppm, ident, f)

    def _view_mod(self, ident: Ident, f: Callable[[View], View]):
        return self._mod(_ident_vpm, ident, f)

    def _mod(self, ctor: Callable, ident: Ident, f: Callable[[View], View]):
        def g(path):
            return Task.now(Right(path.map_view(f)))
        return ctor(ident) / g

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
        opt = options + ('target', ident) + ('shell', shell)
        cmd_runner = self._run_command(command, opt)
        shell_runner = TmuxRunShell(shell, Map())
        return cmd_runner.cons(shell_runner)

    def _pinned_panes(self, ident):
        def layout(l):
            target = l.panes.find(__.has_ident(ident))
            sub = (l.layouts // layout)
            add = (List() if sub.empty and target.empty else
                   l.panes.filter(_.pin))
            return sub + add
        return (self.state.windows / _.root // layout) / _.ident

    def _main_command(self, cmd_ident: Ident):
        holder = lambda cmd: cmd.shell // self.data.shell | cmd
        return self.data.command(cmd_ident) / holder


class Plugin(MyoComponent):
    Transitions = TmuxTransitions

    @lazy
    def socket(self):
        return self.vim.vars.p('tmux_socket') | None

    @property
    def native_server(self):
        return NativeServer(socket_name=self.socket)

    @property
    def server(self):
        return Server(self.native_server)

    @property
    def layouts(self):
        return LayoutFacade(self.server)

    @property
    def panes(self):
        return PaneFacade(self.server)

    @property
    def views(self):
        return ViewFacade(self.server)

    def new_state(self):
        return TmuxState(server=self.server)

    @lazy
    def watcher(self):
        interval = self.vim.vars.p('tmux_watcher_interval') | 1.0
        return Watcher(self, interval=interval)

__all__ = ('Plugin',)
