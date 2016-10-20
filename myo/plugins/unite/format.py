from functools import singledispatch  # type: ignore

from myo.command import ShellCommand, TransientCommand


@singledispatch
def unite_format(obj):
    return str(obj)

unite_format_str_command = '[{name}] {line}'


def _format_cmd(name, display_name, line):
    word = unite_format_str_command.format(name=display_name, line=line)
    return dict(word=word, name=name)


@unite_format.register(ShellCommand)
def unite_format_command(cmd):
    return _format_cmd(cmd.name, cmd.name, cmd.line)


@unite_format.register(TransientCommand)
def unite_format_transient_command(cmd):
    return _format_cmd(cmd.name, cmd.command.name, cmd.line)

__all__ = ('unite_format',)
