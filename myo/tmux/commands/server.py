from myo.components.tmux.io import TmuxIO


def kill_server() -> TmuxIO[None]:
    return TmuxIO.write('kill-server')

__all__ = ('kill_server',)
