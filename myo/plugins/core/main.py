from trypnv.machine import may_handle, io, Error

import tryp
from tryp import __, F

from myo.state import MyoComponent, MyoTransitions
from myo.plugins.core.dispatch import VimDispatcher
from myo.plugins.core.message import StageI, Initialized


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

        @may_handle(Error)
        def error(self):
            m = self.msg.message
            handler = (F(self.log.caught_exception, 'transition') if
                       tryp.development and isinstance(m, Exception) else
                       self.log.error)
            handler(m)

__all__ = ('Plugin',)
