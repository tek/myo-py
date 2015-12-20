from typing import Union  # type: ignore
from pathlib import Path

import pyrsistent  # type: ignore

from fn import _  # type: ignore

from lenses import lens

from trypnv.machine import Data

from myo.command import Commands, Command
from myo.view import Views, View


def field(tpe, **kw):
    return pyrsistent.field(type=tpe, mandatory=True, **kw)


class Env(pyrsistent.PRecord, Data):
    config_path = field(Path)
    initialized = field(bool, initial=False)
    commands = field(Commands, initial=Commands())
    views = field(Views, initial=Views())

    @property
    def _cmdlens(self):
        return lens(self).commands

    @property
    def _viewlens(self):
        return lens(self).views

    def __add__(self, item: Union[Command, View]):
        lens = (
            self._cmdlens if isinstance(item, Command) else
            self._viewlens if isinstance(item, View) else None
        )
        return lens.modify(_ + item)

__all__ = ['Env']
