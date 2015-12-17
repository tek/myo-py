from pathlib import Path

from trypnv.machine import Data

import pyrsistent  # type: ignore

from myo.command import Commands
from myo.view import Views


def field(tpe, **kw):
    return pyrsistent.field(type=tpe, mandatory=True, **kw)


class Env(pyrsistent.PRecord, Data):
    config_path = field(Path)
    initialized = field(bool, initial=False)
    commands = field(Commands, initial=Commands())
    views = field(Views, initial=Views())

__all__ = ['Env']
