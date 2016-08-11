import asyncio

from psutil import Process

from trypnv.record import list_field, bool_field, field
from trypnv.machine import may_handle, handle, Transitions, message, RunTask
from trypnv import StateMachine

from tryp import Empty, Try, __, List, L, _
from tryp.task import Task

from myo.record import Record
from myo.plugins.tmux.messages import WatchCommand
from myo.command import Command
from myo.ui.tmux.pane import Pane


class WatcherState(Record):
    commands = list_field()
    watching = bool_field()

    def remove(self, cmds):
        return self.set(commands=self.commands.remove_all(cmds))


class WatchedCommand(Record):
    command = field(Command)
    pane = field(Pane)


Start = message('Start')
Stop = message('Stop')
Tick = message('Tick')
Terminated = message('Terminated', 'command', 'pane')


class WatcherTransitions(Transitions):

    @property
    async def _sleep(self):
        await asyncio.sleep(self.machine.interval)
        return Empty()

    @may_handle(WatchCommand)
    def watch_command(self):
        wc = WatchedCommand(command=self.msg.command, pane=self.msg.pane)
        return self.data.append1.commands(wc), Start()

    @handle(Start)
    def start_rec(self):
        return self.data.watching.no.maybe_call(
            lambda: (self.data.set(watching=True), Tick().pub))

    @may_handle(Stop)
    def stop_rec(self):
        return self.data.set(watching=False)

    @handle(Tick)
    def tick(self):
        return self.data.watching.maybe_call(self._tick)

    def _tick(self):
        restart = List(self._sleep, Tick().pub)
        done = self.data.commands.flat_map(self._check_proc)
        data = self.data.remove(done)
        term_msg = lambda wc: Terminated(wc.command, wc.pane)
        term = done / term_msg / L(Task.call)(self.machine.bubble, _) / RunTask
        return term.cons(data) + restart

    def _check_proc(self, wc):
        proc = wc.pane.pid // (lambda a: Try(Process, a).to_maybe)
        return proc.exists(__.is_running()).no.maybe(wc)


class Watcher(StateMachine):
    _data_type = WatcherState

    Transitions = WatcherTransitions

    def __init__(self, machine, interval: float) -> None:
        super().__init__('tmux watcher', List(), machine)
        self.machine = machine
        self.interval = interval

    @property
    def init(self):
        return WatcherState()

__all__ = ('Watcher',)
