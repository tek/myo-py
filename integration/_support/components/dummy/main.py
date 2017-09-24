from amino import Empty

from ribosome.machine.transition import may_handle
from ribosome.machine.messages import Stage1
from ribosome.machine.state import Component

from myo.components.command.message import CommandExecuted
from myo.command import CommandJob

from integration._support.components.dummy.dispatcher import DummyDispatcher, DummyRun


class Dummy(Component):

    @may_handle(Stage1)
    def stage_i(self):
        return self.data + DummyDispatcher()

    @may_handle(DummyRun)
    def run(self):
        cmd = self.msg.cmd
        job = cmd if isinstance(cmd, CommandJob) else CommandJob(command=cmd)
        return CommandExecuted(job, Empty()).pub

__all__ = ('Dummy',)
