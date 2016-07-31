from typing import Union
from pathlib import Path

from fn import _

from tryp import Map

from trypnv.data import field, Data

from myo.command import Commands, Command
from myo.view import Views, View
from myo.dispatch import Dispatchers, Dispatcher


class Env(Data):
    config_path = field(Path)
    initialized = field(bool, initial=False)
    commands = field(Commands, initial=Commands())
    views = field(Views, initial=Views())
    dispatchers = field(Dispatchers, initial=Dispatchers())

    def __add__(self, item: Union[Command, View, Dispatcher]):
        name = (
            'commands' if isinstance(item, Command) else
            'views' if isinstance(item, View) else
            'dispatchers' if isinstance(item, Dispatcher) else
            None
        )
        return self.mod(name, _ + item)

    def command(self, name: str):
        return self.commands[name]

    def dispatch_message(self, cmd: Command, options: Map):
        return self.dispatchers.message(cmd, options)

__all__ = ('Env')
