from amino import do, Do, Maybe, IO, Lists

from chiasma.io.compute import TmuxIO

from psutil import Process
from chiasma.commands.pane import pane_pid

from myo.data.command import Pid


@do(TmuxIO[Maybe[Pid]])
def process_pid(pane_id: int) -> Do:
    shell_pid = yield pane_pid(pane_id)
    proc = yield TmuxIO.from_io(IO.delay(Process, shell_pid))
    children = yield TmuxIO.from_io(IO.delay(proc.children))
    return Lists.wrap(children).head.map(lambda a: a.pid).map(Pid)


__all__ = ('process_pid',)
