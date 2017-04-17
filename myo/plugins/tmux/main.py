from typing import Callable

from amino import (List, _, __, Just, Map, Right, Empty, Either, Boolean, I,
                   Maybe)
from amino.lazy import lazy
from amino.task import Task
from amino.anon import L

from ribosome.machine import may_handle, handle, Quit, Nop, Message
from ribosome.machine.base import UnitTask, DataTask
from ribosome.machine.transition import Error, Fatal

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.tmux.message import (TmuxOpen, TmuxRunCommand, TmuxCreatePane,
                                      TmuxCreateLayout, TmuxCreateSession,
                                      TmuxSpawnSession, TmuxFindVim, TmuxInfo,
                                      TmuxLoadDefaults, TmuxClosePane,
                                      TmuxRunLineInShell, StartWatcher,
                                      WatchCommand, QuitWatcher, TmuxPack,
                                      TmuxPostOpen, TmuxFixFocus, TmuxMinimize,
                                      TmuxRestore, TmuxToggle, TmuxFocus,
                                      TmuxOpenOrToggle, TmuxKill,
                                      UpdateVimWindow, TmuxRunTransient,
                                      TmuxPostCommand, TmuxRebootCommand)
from myo.plugins.core.main import StageI
from myo.ui.tmux.pane import Pane, VimPane, PaneData
from myo.ui.tmux.layout import LayoutDirections, Layout, VimLayout
from myo.ui.tmux.session import Session, VimSession
from myo.ui.tmux.server import Server, NativeServer
from myo.util import Ident
from myo.ui.tmux.window import VimWindow
from myo.plugins.core.message import AddDispatcher, Resized, Initialized
from myo.plugins.tmux.dispatch import TmuxDispatcher
from myo.ui.tmux.view_path import LayoutPathMod, PanePathMod, ViewPathMod
from myo.ui.tmux.data import TmuxState
from myo.plugins.command.message import SetShellTarget, CommandExecuted
from myo.command import Command, Shell, default_signals, CommandJob
from myo.plugins.tmux.watcher import Watcher, Terminated
from myo.ui.tmux.facade.main import TmuxFacade
from myo.ui.tmux.util import format_state


invalid_pane_name = 'invalid pane name: {}'


class TmuxTransitions(MyoTransitions):

    @property
    def tmux(self):
        return TmuxFacade(self.state, self.machine.socket, self.options)

    @property
    def server(self):
        return self.machine.server

    def record_lens(self, tpe, name):
        return (
            self.state.pane_lens_ident(name)
            if tpe == 'pane' else
            self.state.layout_lens_ident(name)
            if tpe == 'layout' else
            Empty()
        )

    @may_handle(StageI)
    def stage_1(self):
        ''' Initialize the state. If it doesn't exist, Env will create
        it using the constructor function supplied in *Plugin.state*
        '''
        default = self.pflags.tmux_use_defaults.maybe(TmuxLoadDefaults())
        msgs = List(AddDispatcher(), self.with_sub(self.state), TmuxFindVim(),
                    UpdateVimWindow())
        watcher = (List() if self.vim.vars.p('tmux_no_watcher').true else
                   List(StartWatcher()))
        return msgs + default.to_list + watcher

    @may_handle(Initialized)
    def initialized(self):
        return self.with_sub(self.state.set(initialized=True))

    @may_handle(AddDispatcher)
    def add_dispatcher(self):
        return self.data + TmuxDispatcher()

    @may_handle(TmuxFindVim)
    def find_vim(self):
        id = (
            self.vim.vars.pi('tmux_force_vim_pane_id')
            .o(lambda: self.native_vim_pane // _.id_i)
        )
        wid = (
            self.vim.vars.pi('tmux_force_vim_win_id')
            .o(lambda: self.native_vim_pane // _.window_id_i)
            .to_either('no vim win id')
        )
        sid = (
            self.vim.vars.pi('tmux_force_vim_session_id')
            .o(lambda: self.native_vim_pane // _.session_id_i)
            .to_either('no vim session id')
        )
        vim_w = self.vim.vars.p('tmux_vim_width').or_else(Just(88))
        pane = VimPane(id=id.to_maybe, window_id=wid, session_id=sid)
        vim_layout = VimLayout(name=VimPane.pane_name,
                               direction=LayoutDirections.vertical,
                               panes=List(pane), min_size=vim_w,
                               weight=Just(0.0001))
        root = Layout(name='root',
                      direction=LayoutDirections.horizontal,
                      layouts=List(vim_layout))
        win = VimWindow(id=wid.to_maybe, root=root)
        session = VimSession(id=sid.to_maybe, windows=List(win))
        new_state = self.state.append1.sessions(session)
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
        return UnitTask(Task.delay(self.machine.watcher.start))

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
            L(self.tmux.add_layout_to_layout)(opts.get('parent'), _) /
            self.with_sub
        )

    @handle(TmuxCreatePane)
    def create_pane(self):
        opts = self.msg.options
        return (
            self._from_opt(Pane, name=self.msg.name) //
            L(self.tmux.add_pane_to_layout)(opts.get('parent'), _) /
            self.with_sub
        )

    @may_handle(TmuxOpen)
    def open(self):
        name = self.msg.name
        opt = self.msg.options
        pinned = opt.get('pinned').exists(I)
        def open():
            return (
                self.tmux.open_pane_ppm(name),
                (Nop() if pinned else TmuxPostOpen(name, opt - 'pinned').pub)
            )
        return (
            open()
            if self.tmux.view_exists(name) else
            Error(invalid_pane_name.format(name))
        )

    @may_handle(TmuxPostOpen)
    def open_pinned(self):
        return (
            self.tmux.pinned_panes(self.msg.ident) /
            L(TmuxOpen)(_, Map(pinned=True))
        ) + List(TmuxFixFocus(self.msg.ident), TmuxPack().pub.at(1))

    @handle(TmuxFixFocus)
    def fix_focus(self):
        return self.tmux.fix_focus(self.msg.pane, VimPane.pane_name) / UnitTask

    @handle(TmuxFocus)
    def focus(self):
        return self.tmux.focus(self.msg.pane) / UnitTask

    @handle(TmuxClosePane)
    def close(self):
        return (self.tmux.close_pane_ppm(self.msg.name) &
                Right(TmuxPack().pub.at(1)))

    @handle(TmuxRunCommand)
    def run_command(self) -> Maybe[Message]:
        job = self.msg.job
        options = self.msg.options
        shell = (options.get('shell')
                 .o(job.shell) //
                 self.data.shell)
        return shell.to_maybe.cata(
            L(self._run_in_shell)(job, _, options),
            L(self._run_command)(job, options)
        )

    @handle(TmuxRebootCommand)
    def tmux_reboot_command(self):
        return ((self.msg.job.command.target / TmuxClosePane) &
                Just(TmuxRunCommand(self.msg.job)))

    @handle(SetShellTarget)
    def set_shell_target(self) -> Maybe[Message]:
        target = self._pane(self.msg.target) / _.uuid
        setter = __.modify(__.set(target=target))
        msg = 'cannot set shell target {} for {}: pane not found'
        return (
            target
            .to_either(msg.format(self.msg.target, self.msg.shell.name)) //
            (lambda a: self.data.command_lens(self.msg.shell.uuid)) /
            setter
        )

    @handle(TmuxRunLineInShell)
    def run_line_in_shell(self):
        opt = self.msg.options
        return (
            opt.get('target') /
            (lambda a: Command(name='temp', line=a)) /
            L(self._run_in_shell)(_, self.msg.shell, opt)
        )

    @may_handle(TmuxRunTransient)
    def run_transient(self):
        return TmuxRunCommand(self.msg.cmd, options=self.msg.options)

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
        return QuitWatcher(), UnitTask(self.tmux.close_all)

    @may_handle(QuitWatcher)
    def quit_watcher(self):
        return UnitTask(Task.delay(self.machine.watcher.stop))

    @may_handle(TmuxInfo)
    def info(self):
        self.log.info('\n'.join(format_state(self.state)))

    @may_handle(Terminated)
    def terminated(self):
        return self.tmux.pane_mod(self.msg.pane.uuid, __.set(pid=Empty()))

    @may_handle(TmuxPack)
    def pack(self):
        return UnitTask(self.tmux.pack_sessions), UpdateVimWindow()

    @handle(UpdateVimWindow)
    def update_vim_window(self):
        def update_vim_window(sess, win_lens):
            win = win_lens.get()
            w = self.tmux.native_window(sess, win)
            return (
                (w / _.size) /
                Just /
                win.setter.size /
                win_lens.set /
                self.with_sub
            )
        return ((self.state.vim_session & self.state.vim_window_lens)
                .flat_map2(update_vim_window))

    @handle(Resized)
    def resized(self):
        def check(win, adapter):
            return win.size.contains(adapter.size).no.maybe(TmuxPack())
        return (
            self.state.initialized
            .flat_maybe((self.state.vim_window & self.tmux.native_vim_window))
            .flat_map2(check)
        )

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
            self.tmux.view_open(name) /
            __.c(TmuxToggle(name), TmuxOpen(name))
        )

    @may_handle(TmuxKill)
    def kill(self):
        signals = self.msg.options.get('signals') | default_signals
        return self.tmux.kill_process(self.msg.pane, signals) / __.lmap(Fatal)

    @may_handle(TmuxPostCommand)
    def post_command(self):
        log_path = self._pane(self.msg.pane_ident) // _.log_path
        return CommandExecuted(self.msg.job, log_path).pub

    def _minimize(self, f):
        return self.tmux.view_mod(self.msg.pane, f), TmuxPack().pub.at(1)

    def _state_task(self,
                    f: Callable[[TmuxState], Task[Either[str, TmuxState]]],
                    options=Map()):
        cb = lambda d: f(self._state(d)) / __.map(L(self._with_sub)(d, _))
        return DataTask(_ // cb)

    def _run_vpm(self, vpm):
        return self._state_task(vpm.run, self.msg.options)

    def _pane(self, ident: Ident):
        return self.state.pane(ident)

    @property
    def _vim_pane(self):
        return self._pane(VimPane.pane_name)

    def _pane_uuid(self, ident: Ident):
        return self._pane(ident) / _.uuid

    def _default_pane_name(self):
        return 'make'

    @property
    def _vim_pid(self):
        return self.vim.call('getpid').to_either('no pid')

    @lazy
    def native_vim_pane(self):
        return self._vim_pid // self._find_vim_pane_by_pid

    def _find_vim_pane_by_pid(self, vim_pid: int) -> Maybe[PaneData]:
        return (
            self.server.pane_data
            .find(__.command_pids.exists(__.contains(vim_pid)))
        )

    def _run_command(self, job: CommandJob, opt):
        args = opt.get('args') | job.args
        return (
            job.line
            .resolve(self.vim, *args) /
            L(self._run_command_line)(job, _, opt)
        )

    def _run_command_line(self, job: CommandJob, line, opt):
        command = job.command
        kill = opt.get('kill') | command.kill
        signals = opt.get('signals') / List.wrap | command.signals
        pane_ident = (opt.get('target').o(command.target) |
                      self._default_pane_name)
        in_shell = Boolean('shell' in opt)
        def watch(path):
            msg = WatchCommand(job, path.view)
            return Task.call(self.machine.watcher.send, msg)
        runner, is_open = self.tmux.run_command_ppm(pane_ident, line, in_shell,
                                                    kill, signals)
        post = is_open.no.m(TmuxPostOpen(pane_ident, opt)).to_list
        return post.cons(runner % watch).cat(TmuxPostCommand(job, pane_ident))

    def _run_in_shell(self, job: CommandJob, shell: Shell, options: Map):
        ident = shell.target | self._default_pane_name
        opt = options + ('target', ident) + ('shell', shell)
        return (self._run_command(job, opt) /
                __.cons(TmuxRunCommand(CommandJob(command=shell), Map())))

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

    def new_state(self):
        return TmuxState()

    @lazy
    def watcher(self):
        interval = self.vim.vars.p('tmux_watcher_interval') | 1.0
        return Watcher(self, interval=interval)

__all__ = ('Plugin',)
