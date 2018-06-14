from amino import Path

from ribosome.nvim.io.state import NS

from myo.components.command.compute.tpe import CommandRibosome


def project_relative_path(path: Path) -> NS[CommandRibosome, str]:
    return NS.pure(str(path.relative_to(Path.cwd())))


__all__ = ('project_relative_path',)
