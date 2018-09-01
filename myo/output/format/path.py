from amino import Path, do, Do, IO

from ribosome.nvim.io.state import NS

from myo.components.command.compute.tpe import CommandRibosome


@do(NS[CommandRibosome, str])
def project_relative_path(path: Path) -> Do:
    rel = yield NS.from_io(IO.delay(path.relative_to, Path.cwd()).recover(lambda a: path))
    return str(rel)


__all__ = ('project_relative_path',)
