from amino import Empty

from ribosome.machine import may_handle

from myo.state import MyoTransitions, MyoComponent
from myo.plugins.core.message import StageI
from myo.plugins.command.message import CommandExecuted

from integration._support.plugins.dummy.dispatcher import (DummyDispatcher,
                                                           DummyRun)


class DummyTransitions(MyoTransitions):

    @may_handle(StageI)
    def stage_i(self):
        return self.data + DummyDispatcher()

    @may_handle(DummyRun)
    def run(self):
        return CommandExecuted(self.msg.cmd, Empty()).pub


class Plugin(MyoComponent):
    Transitions = DummyTransitions

    def new_state(self):
        pass

__all__ = ('Plugin',)
