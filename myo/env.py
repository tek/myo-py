from typing import Union, Callable
from pathlib import Path

from lenses import lens

from amino import Map, _, __

from ribosome.data import field, Data

from myo.command import Commands, Command
from myo.view import Views, View
from myo.dispatch import Dispatchers, Dispatcher
from myo.ui.tmux.util import Ident


class Env(Data):
    config_path = field(Path)
    initialized = field(bool, initial=False)
    commands = field(Commands, initial=Commands())
    views = field(Views, initial=Views())
    dispatchers = field(Dispatchers, initial=Dispatchers())

    def cat(self, item: Union[Command, View, Dispatcher]):
        name = (
            'commands' if isinstance(item, Command) else
            'views' if isinstance(item, View) else
            'dispatchers' if isinstance(item, Dispatcher) else
            None
        )
        return self.mod(name, _ + item)

    __add__ = cat

    def command(self, name: str):
        return self.commands[name]

    def shell(self, name: str):
        return self.commands.shell(name)

    def dispatch_message(self, cmd: Command, options: Map):
        return self.dispatchers.message(cmd, options)

    def _lens(self, getter: Callable, ident: Ident):
        deep = getter(getter(self)).find_lens_pred(__.has_ident(ident))
        return deep / getter(getter(lens(self))).add_lens

    def command_lens(self, ident: Ident):
        return self._lens(_.commands, ident)

    def transient_command(self, cmd: Command):
        return self.mod('commands', __.transient_command(cmd))

__all__ = ('Env')
