from typing import TypeVar

from amino import Either, __, Maybe, Left, List, Right, Nil, Just, Do, L, Nothing
from amino.do import do

from myo.components.tmux.tmux import TmuxCmd, TmuxCmdResult, TmuxCmdSuccess
from myo.tmux.io.compute import TmuxIO

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
S = TypeVar('S')


__all__ = ()
