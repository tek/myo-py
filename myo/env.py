from typing import Union, Callable
from pathlib import Path

from lenses import lens

from amino import Map, _, __, Either

from ribosome.data import field, Data
from ribosome.record import maybe_field
from ribosome.nvim import NvimFacade, AsyncVimProxy

from myo.command import Commands, Command
from myo.dispatch import Dispatchers, Dispatcher
from myo.util import Ident


class Env(Data):
    vim_facade = maybe_field((NvimFacade, AsyncVimProxy))
    initialized = field(bool, initial=False)
    commands = field(Commands, initial=Commands())
    dispatchers = field(Dispatchers, initial=Dispatchers())

    @property
    def vim(self) -> NvimFacade:
        return self.vim_facade | (lambda: NvimFacade(None, 'no vim was set in `Env`'))

    def cat(self, item: Union[Command, Dispatcher]):
        name = (
            'commands' if isinstance(item, Command) else
            'dispatchers' if isinstance(item, Dispatcher) else
            None
        )
        return self.mod(name, _ + item)

    __add__ = cat

    def command(self, name: str):
        return self.commands[name]

    def command_or_job(self, name: str):
        return self.commands.command_or_job(name)

    def shell(self, name: str):
        return self.commands.shell(name)

    def dispatch_message(self, cmd: Command, options: Map):
        return self.dispatchers.message(cmd, options)

    def _lens(self, getter: Callable, ident: Ident):
        return (
            getter(getter(self))
            .find_lens_pred(__.has_ident(ident))
            .to_either('no command with ident {} found'.format(ident)) /
            getter(getter(lens(self))).add_lens
        )

    def command_lens(self, ident: Ident):
        return self._lens(_.commands, ident)

    def transient_command(self, cmd: Command):
        return self.mod('commands', __.transient_command(cmd))

__all__ = ('Env',)
