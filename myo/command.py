import abc
from functools import singledispatch  # type: ignore

from amino import Path, __, Just, List, L, Maybe, _, Map

from ribosome.record import list_field, field, maybe_field, bool_field
from ribosome.util.callback import parse_callback_spec

from myo.record import Record, Named
from myo.util import ident_field, Ident
from myo.logging import Logging


default_signals = List('int', 'term', 'kill')


class Line(Logging, metaclass=abc.ABCMeta):

    def __init__(self, line) -> None:
        self.line = line

    @abc.abstractmethod
    def resolve(self, vim) -> Maybe[str]:
        ...


class StrictLine(Line):

    def resolve(self, vim):
        return Just(self.line)


class EvalLine(Line):

    def resolve(self, vim):
        return parse_callback_spec(self.line) // __(vim)


class Command(Named):
    log_path = maybe_field(Path)
    parser = maybe_field(str)
    transient = bool_field()
    langs = list_field()
    kill = bool_field()
    signals = list_field(str, initial=default_signals)
    eval = bool_field()

    @property
    def _str_extra(self):
        return super()._str_extra.cat_m(self.langs.empty.no.m(self.langs))

    @property
    def _str_extra_named(self):
        return Map(eval=self.eval)

    @property
    def desc(self):
        info = self._info.mk_string(' ∘ ')
        tail = ': {}'.format(info) if info else ''
        return '{} {}{}'.format(self._type_desc, self.name, tail)

    @property
    def _info_fields(self):
        return List('langs', 'parser', 'log_path')

    @property
    def _info(self) -> List[str]:
        return self._info_fields // self._field_info

    def _field_info(self, name: str):
        v = getattr(self, name)
        fmt = '⎡{} -> {}⎤'.format
        if isinstance(v, Maybe):
            return v / L(fmt)(name, _)
        elif isinstance(v, List):
            return v.empty.no.maybe(fmt(name, v.mk_string(',')))
        else:
            return Just(fmt(name, v))

    @property
    def _type_desc(self):
        return 'C'

    @property
    def target_id(self) -> Ident:
        return self.ident


class VimCommand(Command):

    @property
    def _type_desc(self):
        return 'VC'


class ShellCommand(Command):
    line = field(str)
    shell = ident_field()

    @property
    def _type_desc(self):
        return 'SC'

    @property
    def _info_fields(self):
        return super()._info_fields + List('shell')

    @property
    def effective_line(self):
        tpe = EvalLine if self.eval else StrictLine
        return tpe(self.line)

    @property
    def target_id(self):
        return self.shell | self.ident


class Shell(ShellCommand):
    target = ident_field()

    @property
    def _type_desc(self):
        return 'S'


class TransientCommand(Command):
    command = field(Command)
    line = field(str)

    def __new__(cls, prefix='transient', transient=None, command=None,
                name=None, **kw):
        name = name or '{}_{}_{}'.format(prefix, command.name,
                                         List.random_string(5))
        return super().__new__(cls, name=name, transient=True, command=command,
                               **kw)

    @property
    def _str_extra(self):
        return super()._str_extra.cat(self.command)

    @property
    def effective(self):
        return self.command.set(name=self.name, line=self.line)

    @property
    def target_id(self):
        return self.command.target_id


@singledispatch
def _history_cmp(cmd):
    return cmd.name


@_history_cmp.register(TransientCommand)
def _history_cmp_transient(cmd):
    return '{}|{}'.format(cmd.command.name, cmd.line)


class Commands(Record):
    commands = list_field()
    history = list_field()
    transient_cmd = maybe_field(Command)

    def __add__(self, command: Command):
        return self.append1.commands(command)

    def __getitem__(self, ident: Ident):
        return (
            self.commands.find(__.has_ident(ident))
            .o(lambda: self.history.find(__.has_ident(ident)))
            .to_either('no command with ident {}'.format(ident))
        )

    @property
    def _str_extra(self):
        return super()._str_extra.cat(self.commands)

    def shell(self, ident):
        pred = lambda a: isinstance(a, Shell) and a.has_ident(ident)
        return self.commands.find(pred)

    def add_history(self, cmd):
        new = self.history.cons(cmd).distinct_by(_history_cmp)
        return self.set(history=new)

    def transient_command(self, cmd):
        return self.set(transient_cmd=Just(cmd))

    @property
    def latest_command(self):
        return self.history.head

__all__ = ('Commands', 'Command', 'VimCommand', 'ShellCommand', 'Shell',
           'TransientCommand')
