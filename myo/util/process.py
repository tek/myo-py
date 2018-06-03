from amino import do, Do, IO

from psutil import Process

from myo.data.command import Pid


def process(pid: Pid) -> IO[Process]:
    return IO.delay(Process, pid.value)


@do(IO[None])
def kill_process(pid: Pid, signal: int=9) -> Do:
    proc = yield process(pid)
    yield IO.delay(proc.kill)


__all__ = ('process', 'kill_process',)
