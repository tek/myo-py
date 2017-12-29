from amino import List, Dat, Nil
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from myo.components.command.trans.add import add_system_command
from myo.data.command import Command


class CommandData(Dat['CommandData']):

    @staticmethod
    def cons(
            commands: List[Command]=Nil,
    ) -> 'CommandData':
        return CommandData(
            commands,
        )

    def __init__(self, commands: List[Command]) -> None:
        self.commands = commands


command = Component.cons(
    'command',
    state_ctor=CommandData.cons,
    request_handlers=List(
        RequestHandler.trans_cmd(add_system_command)(json=true),
    ),
)

__all__ = ('command',)
