from amino import Empty

from ribosome.machine.transition import may_handle
from ribosome.machine.messages import Stage1

from myo.state import MyoTransitions, MyoComponent
from myo.plugins.command.message import CommandExecuted
from myo.command import CommandJob

from integration._support.plugins.dummy.dispatcher import (DummyDispatcher,
                                                           DummyRun)


class DummyTransitions(MyoTransitions):

    @may_handle(Stage1)
    def stage_i(self):
        return self.data + DummyDispatcher()

    @may_handle(DummyRun)
    def run(self):
        cmd = self.msg.cmd
        job = cmd if isinstance(cmd, CommandJob) else CommandJob(command=cmd)
        return CommandExecuted(job, Empty()).pub


class Plugin(MyoComponent):
    Transitions = DummyTransitions

    def new_state(self):
        pass

__all__ = ('Plugin',)
