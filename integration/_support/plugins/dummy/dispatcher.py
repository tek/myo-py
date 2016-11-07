from ribosome.machine import json_message

from myo.dispatch import Dispatcher

DummyRun = json_message('DummyRun', 'cmd')


class DummyDispatcher(Dispatcher):

    def can_run(self, cmd):
        return True

    def message(self, cmd, options):
        return DummyRun(cmd, options)

__all__ = ('DummyDispatcher',)
