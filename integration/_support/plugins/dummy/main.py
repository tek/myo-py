from ribosome.machine import may_handle

from myo.state import MyoTransitions, MyoComponent
from myo.plugins.core.message import StageI

from integration._support.plugins.dummy.dispatcher import DummyDispatcher


class DummyTransitions(MyoTransitions):

    @may_handle(StageI)
    def stage_i(self):
        return self.data + DummyDispatcher()


class Plugin(MyoComponent):
    Transitions = DummyTransitions

__all__ = ('Plugin',)