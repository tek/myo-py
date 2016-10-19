from functools import singledispatch  # type: ignore

from myo.command import Command, TransientCommand


@singledispatch
def unite_format(obj):
    return str(obj)


@unite_format.register(Command)
def unite_format_command(cmd):
    return dict(word=cmd.name, name=cmd.name)


@unite_format.register(TransientCommand)
def unite_format_transient_command(cmd):
    line = '{} {}'.format(cmd.command.name, cmd.line)
    return dict(word=line, name=cmd.name)

__all__ = ('unite_format',)
