from trypnv.machine import may_handle, message, io

from tryp import __

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher

StageI = message('StageI')
StageII = message('StageII')
Initialized = message('Initialized')


class Plugin(MyoComponent):

    class Transitions(MyoTransitions):

        @may_handle(StageI)
        def stage_1(self):
            return Initialized().pub.at(1)

        @may_handle(Initialized)
        def initialized(self):
            started = io(__.set_pvar('started', True))
            return (self.data.set(initialized=True) + VimDispatcher(self.vim),
                    started)

__all__ = ('Plugin', 'StageI', 'StageII', 'Initialized')
