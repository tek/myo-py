from amino import List, Dat, Nil, Either, _
from amino.boolean import true

from chiasma.util.id import Ident

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

    def command_by_ident(self, ident: Ident) -> Either[str, Command]:
        return self.commands.find(_.ident == ident).to_either(f'no command `{ident}`')


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
