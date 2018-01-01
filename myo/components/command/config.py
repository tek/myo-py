from amino import List, Dat, Nil
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from myo.components.command.trans.add import add_system_command, add_vim_command, add_shell_command
from myo.data.command import Command
from myo.components.command.trans.run import run_command
from myo.config.component import MyoComponent


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
        RequestHandler.trans_cmd(add_vim_command)(json=true),
        RequestHandler.trans_cmd(add_system_command)(json=true),
        RequestHandler.trans_cmd(add_shell_command)(json=true),
        RequestHandler.trans_cmd(run_command)(json=true),
    ),
    config=MyoComponent.cons(),
)

__all__ = ('command',)
