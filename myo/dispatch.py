from abc import ABCMeta, abstractmethod

from tryp import __, Left, _
from trypnv.machine import Message
from trypnv.record import list_field, Record

from myo.command import Command


class Dispatcher(metaclass=ABCMeta):

    @abstractmethod
    def can_run(self, cmd: Command) -> bool:
        ...

    def message(self, cmd: Command) -> Message:
        ...


class Dispatchers(Record):
    dispatchers = list_field()

    def message(self, cmd: Command):
        eligible = self.dispatchers.filter(__.can_run(cmd))
        if eligible.length > 1:
            msg = 'Multiple dispatchers for {}: {}'
            return Left(msg.format(cmd, eligible))
        else:
            return (
                eligible
                .head
                .to_either('Cannot dispatch {}'.format(cmd)) /
                __.message(cmd)
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
