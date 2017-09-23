from abc import ABCMeta, abstractmethod

from amino import __, Left, _, Map
from ribosome.machine.message_base import Message
from ribosome.record import list_field, Record

from myo.command import Command
from myo.logging import Logging


class Dispatcher(Logging, metaclass=ABCMeta):

    @abstractmethod
    def can_run(self, cmd: Command) -> bool:
        ...

    @abstractmethod
    def message(self, cmd: Command, options: Map) -> Message:
        ...


class Dispatchers(Record):
    dispatchers = list_field()

    def message(self, cmd: Command, options: Map):
        eligible = self.dispatchers.filter(__.can_run(cmd))
        if eligible.length > 1:
            msg = 'Multiple dispatchers for {}: {}'
            return Left(msg.format(cmd, eligible))
        else:
            return (
                eligible
                .head
                .to_either('Cannot dispatch {}'.format(cmd)) /
                __.message(cmd, options)
            )

    def __add__(self, dispatcher: Dispatcher):
        return self.append.dispatchers([dispatcher])

    def __getitem__(self, name):
        return self.dispatchers.find(_.name == name)

    def __str__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ','.join(map(repr, self.dispatchers))
        )

__all__ = ('Dispatchers', 'Dispatcher')
