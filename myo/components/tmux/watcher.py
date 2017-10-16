from typing import Tuple, Generator, Type, Callable, Any
from concurrent import futures
from concurrent.futures import Future

from psutil import Process

from ribosome.record import list_field, bool_field, field, maybe_field
from ribosome.machine.transition import may_handle
from ribosome.machine.message_base import message, Message
from ribosome.machine.state import ComponentMachine, SubTransitions
from ribosome.machine.messages import Fork, Quit, Error
from ribosome.machine.machine import Machine
from ribosome.nvim import NvimFacade, NvimIO
from ribosome.machine import trans
from ribosome.nvim.io import NvimIOState

from fn.recur import tco

from lenses import lens

from amino import Try, __, List, _, Just, Nil, Nothing, Id, Maybe, Boolean, Map, Either, Right, Left
from amino.io import IO
from amino.do import tdo
from amino.state import StateT, State, MaybeState
from amino.func import ReplaceVal

from myo.record import Record
from myo.components.tmux.message import WatchCommand
from myo.command import CommandJob
from myo.ui.tmux.pane import Pane
from myo import Logging, Env
from myo.ui.tmux.facade.main import TmuxFacade
from myo.util import Ident
from myo.ui.tmux.data import TmuxState


class WatcherState(Record):
    started = list_field()
    running = list_field()
    watching = bool_field()
    wait = maybe_field(Future)

    def remove_started(self, cmds: List['WatchedCommand']) -> 'WatcherState':
        return self.set(started=self.started.remove_all(cmds))

    def remove_running(self, cmds: List['WatchedCommand']) -> 'WatcherState':
        return self.set(running=self.running.remove_all(cmds))

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.started, self.running, self.watching, self.wait)


class WatchedCommand(Record):
    command = field(CommandJob)
    pane = field(Pane)

    @property
    def _str_extra(self) -> List[Any]:
        return List(self.command)

    @property
    def ident(self) -> Ident:
        return self.pane.ident

Start = message('Start')
Stop = message('Stop')
Tail = message('Tail', 'pane')
Terminate = message('Terminate', 'command')
Terminated = message('Terminated', 'command', 'pane')
Started = message('Started', 'command', 'pid')
watcher_name = 'tmux watcher'


class Watch(Logging):

    def __init__(self, state: WatcherState, tmux: TmuxFacade, wait: Future, interval: float) -> None:
        self.state = state
        self.tmux = tmux
        self.wait = wait
        self.interval = interval

    # TODO pending started commands field in state
    # wait for process to appear or time out (2 seconds?), then send message `Started` and promote to running command
    def __call__(self) -> List[Message]:
        result = self.run()
        return Nil if self.wait.cancelled() else result.cat(Start().at(0.6))

    def run(self) -> List[Message]:
        @tco
        def loop() -> List[Message]:
            futures.wait((self.wait,), timeout=self.interval)
            return (
                (False, Nil)
                if self.wait.cancelled() else
                self.tick()
            )
        try:
            return loop()
        except Exception as e:
            self.log.caught_exception('running watcher loop', e)
            return List(Error('Error in command watch loop'))

    def tick(self) -> Tuple[Boolean, List[Message]]:
        result = self.check_started() + self.check_running()
        return result.empty, result

    def check_started(self) -> Tuple[Boolean, List[Message]]:
        return self.state.started.flat_map(self.with_pid).map2(Started)

    @tdo(Either[str, Boolean])
    def with_pid(self, wc: WatchedCommand) -> Generator:
        win, pane = yield self.tmux.pane_window(wc.pane.ident)
        pid = yield win.command_pid(wc.pane).attempt.join
        yield Right((wc, pid))

    def check_running(self) -> Tuple[Boolean, List[Message]]:
        return self.state.running.flat_map(self.check_proc) / Terminate

    def check_proc(self, wc: WatchedCommand) -> Maybe[WatchedCommand]:
        @tdo(Either[Any, Process])
        def check() -> Generator:
            pid = yield wc.pane.pid.to_either(f'no pid for {wc}')
            proc = yield Try(Process, pid)
            yield Right(proc) if proc.is_running() else Left(f'{wc} not running')
        return check().swap.replace(wc)


def new_state() -> WatcherState:
    return WatcherState()


def watcher_state(St: Type[StateT]) -> WatcherState:
    return St.inspect(__.sub_state(watcher_name, new_state))


@tdo(StateT)
def mod_state(St: Type[StateT], f: Callable[[WatcherState], WatcherState]) -> Generator:
    state = yield watcher_state(St)
    yield St.modify(__.with_sub_state(watcher_name, f(state)))


def set_state(St: Type[StateT], new_state: WatcherState) -> StateT:
    return mod_state(St, ReplaceVal(new_state))


@tdo(StateT[Maybe, Env, None])
def stop_watcher() -> Generator:
    state = yield watcher_state(MaybeState)
    wait = yield MaybeState.lift(state.wait)
    yield mod_state(MaybeState, __.set(watching=False, wait=Nothing))
    yield MaybeState.pure(IO.delay(wait.cancel).void)


@tdo(StateT[NvimIO, Env, Watch])
def create_watch() -> Generator:
    env = yield NvimIOState.get()
    settings = yield NvimIOState.inspect(_.settings)
    interval = yield NvimIOState.lift(settings.tmux_watcher_interval.value_or_default)
    state = yield watcher_state(NvimIOState)
    wait = Future()
    new_state = state.set(watching=True, wait=Just(wait))
    yield mod_state(NvimIOState, ReplaceVal(new_state))
    tmux_state = yield NvimIOState.inspect(__.sub_state('tmux', TmuxState))
    socket = yield NvimIOState.lift(env.settings.tmux_socket.value_or_default)
    tmux = TmuxFacade(tmux_state, socket, Map())
    yield NvimIOState.pure(Watch(new_state, tmux, wait, interval))


@tdo(State[Env, List[Message]])
def watch_command(pane: Pane, command: CommandJob) -> Generator:
    wc = WatchedCommand(command=command, pane=pane)
    yield mod_state(State, __.append1.started(wc))
    yield State.pure(List(Tail(pane), Start()))


@tdo(StateT[Id, Env, List[Message]])
def terminate(wc: WatchedCommand) -> Generator:
    state = yield watcher_state(State)
    new_state = state.remove_running(List(wc))
    yield set_state(State, new_state)
    stop = List(Stop()) if new_state.running.empty else Nil
    yield State.pure(stop.cons(Terminated(wc.command, wc.pane)))


@tdo(StateT[Id, Env, None])
def promote_started(cmd: WatchedCommand, pid: int) -> Generator:
    state = yield watcher_state(State)
    new_state = state.append1.running(lens(cmd).pane.pid.set(Just(pid))).remove_started(List(cmd))
    yield set_state(State, new_state)


class WatcherTransitions(SubTransitions):

    @may_handle(WatchCommand)
    def watch_command(self):
        return watch_command(self.msg.pane, self.msg.command)

    @trans.one(Start, trans.st, trans.m)
    @tdo(StateT[NvimIO, Env, Maybe[Message]])
    def start_rec(self) -> Generator:
        state = yield watcher_state(NvimIOState)
        state.wait % __.cancel()
        w = yield create_watch()
        yield NvimIOState.pure(Just(Fork(w).pub))

    @trans.multi(Terminate, trans.st)
    def terminate(self) -> Generator:
        return terminate(self.msg.command)

    @trans.unit(Stop, trans.st, trans.io)
    def stop_rec(self) -> StateT[Maybe, Env, None]:
        return stop_watcher()

    @trans.unit(Started, trans.st)
    def started(self) -> StateT[Id, Env, None]:
        return promote_started(self.msg.command, self.msg.pid)

    @trans.one(Quit)
    def quit(self) -> Message:
        return Stop()

    @may_handle(Tail)
    def tail(self) -> None:
        return


class Watcher(ComponentMachine):

    def __init__(self, vim: NvimFacade, parent: Machine) -> None:
        super().__init__(vim, WatcherTransitions, watcher_name, parent=parent)

__all__ = ('Watcher',)
