from amino import List
from amino.boolean import true

from ribosome.dispatch.component import Component
from ribosome.request.handler.handler import RequestHandler

from myo.components.command.trans.add import add_system_command, add_vim_command, add_shell_command
from myo.components.command.trans.run import run_command
from myo.config.component import MyoComponent
from myo.components.command.data import CommandData
from myo.components.command.trans.parse import parse_pane


command = Component.cons(
    'command',
    state_ctor=CommandData.cons,
    request_handlers=List(
        RequestHandler.trans_cmd(add_vim_command)(json=true),
        RequestHandler.trans_cmd(add_system_command)(json=true),
        RequestHandler.trans_cmd(add_shell_command)(json=true),
        RequestHandler.trans_cmd(run_command)(json=true),
        RequestHandler.trans_cmd(parse_pane)(),
    ),
    config=MyoComponent.cons(),
)

__all__ = ('command',)
