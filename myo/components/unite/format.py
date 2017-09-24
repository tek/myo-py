from functools import singledispatch  # type: ignore

from myo.command import ShellCommand, CommandJob


@singledispatch
def unite_format(obj):
    return str(obj)

unite_format_str_command = '[{name}] {line}'


def _format_cmd(cmd, display_name, line):
    word = unite_format_str_command.format(name=display_name, line=line)
    return dict(word=word, name=cmd.name, ident=str(cmd.ident))


@unite_format.register(ShellCommand)
def unite_format_command(cmd):
    return _format_cmd(cmd, cmd.name, cmd.formatted_line)


@unite_format.register(CommandJob)
def unite_format_transient_command(cmd):
    return _format_cmd(cmd, cmd.command.name, cmd.formatted_line)

__all__ = ('unite_format',)
